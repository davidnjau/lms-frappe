<template>
	<header
		class="sticky top-0 z-10 flex items-center justify-between border-b bg-surface-base px-3 py-2.5 sm:px-5"
	>
		<Breadcrumbs class="h-7" :items="breadcrumbs" />
	</header>
	<div
		v-if="
			readyToRender &&
			(enrollment.data?.length ||
				user.data?.is_moderator ||
				user.data?.is_instructor)
		"
	>
		<iframe
			v-if="!chapter.doc?.is_h5p_package"
			:src="chapter.doc.launch_file"
			class="w-full h-[calc(100vh-3.00rem)]"
		/>
		<div
			v-else
			ref="h5pContainer"
			class="w-full h-[calc(100vh-3.00rem)]"
		/>
	</div>
	<div v-else-if="!enrollment.data?.length">
		<div class="text-center pt-10 px-5 md:px-0 pb-10">
			<div class="text-center">
				<div class="mb-4">
					{{
						__(
							'You are not enrolled in this course. Please enroll to access this lesson.'
						)
					}}
				</div>
				<Button variant="solid" @click="enrollStudent()">
					{{ __('Start Learning') }}
				</Button>
			</div>
		</div>
	</div>
</template>
<script setup>
import {
	Breadcrumbs,
	Button,
	call,
	createDocumentResource,
	createListResource,
	createResource,
	usePageMeta,
} from 'frappe-ui'
import { computed, inject, nextTick, onBeforeMount, ref, watch } from 'vue'
import { useSidebar } from '@/stores/sidebar'
import { sessionStore } from '../stores/session'
import { H5P } from 'h5p-standalone'
import h5pFrameJs from 'h5p-standalone/dist/frame.bundle.js?url'
import h5pFrameCss from 'h5p-standalone/dist/styles/h5p.css?url'

const { brand } = sessionStore()
const sidebarStore = useSidebar()
const user = inject('$user')
const readyToRender = ref(false)
const isSuccessfullyCompleted = ref(false)
const h5pContainer = ref(null)

// If courseRestartOnFailure is true, student has to restart the whole course if failed.
// Otherwise, student could retake the final quiz portion.
// Ideally, this should be configurable along with `Number of failures before course should restart`.
const courseRestartOnFailure = false

const props = defineProps({
	courseName: {
		type: String,
		required: true,
	},
	chapterName: {
		type: String,
		required: true,
	},
})

onBeforeMount(() => {
	sidebarStore.isSidebarCollapsed = true
	setupSCORMAPI()
})

const chapter = createDocumentResource({
	doctype: 'Course Chapter',
	name: props.chapterName,
	auto: true,
	cache: ['chapter', props.chapterName],
	onSuccess(data) {
		progress.submit()
	},
})

const enrollment = createListResource({
	doctype: 'LMS Enrollment',
	fields: ['member', 'course'],
	filters: {
		course: props.courseName,
		member: user.data?.name,
	},
	auto: true,
	cache: ['enrollments', props.courseName, user.data?.name],
})

const getDataFromLMS = (key) => {
	if (key === 'cmi.core.lesson_status') {
		return progress.data?.status === 'Complete' ? 'passed' : 'incomplete'
	} else if (key === 'cmi.launch_data') {
		return progress.data?.scorm_content || ''
	} else if (key === 'cmi.suspend_data') {
		return progress.data?.scorm_content || ''
	}
	return ''
}

let saveTimeout = null
const debouncedSaveProgress = (scormDetails) => {
	if (isSuccessfullyCompleted.value) return
	clearTimeout(saveTimeout)
	saveTimeout = setTimeout(() => {
		if (!isSuccessfullyCompleted.value) saveProgress(scormDetails)
	}, 300)
}

const saveDataToLMS = (key, value) => {
	const isLessonStatus = key === 'cmi.core.lesson_status' && value === 'passed'
	const isCompletionStatus =
		key === 'cmi.completion_status' && value === 'completed'
	const shouldRestart =
		(key === 'cmi.core.lesson_status' && value === 'failed') ||
		(key === 'cmi.completion_status' && value === 'incomplete')

	if (isLessonStatus || isCompletionStatus) {
		if (isSuccessfullyCompleted.value) return
		isSuccessfullyCompleted.value = true
	}

	if (
		isLessonStatus ||
		isCompletionStatus ||
		(shouldRestart && courseRestartOnFailure)
	) {
		saveProgress({
			is_complete: isSuccessfullyCompleted.value,
			scorm_content: '',
		})
		return
	}

	if (key === 'cmi.suspend_data' && !isSuccessfullyCompleted.value) {
		debouncedSaveProgress({
			is_complete: false,
			scorm_content: value,
		})
	}
}

const saveProgress = (scormDetails = null) => {
	call('lms.lms.doctype.course_lesson.course_lesson.save_progress', {
		lesson: chapter.doc.lessons[0].lesson,
		course: props.courseName,
		scorm_details: scormDetails,
	})
}

const progress = createResource({
	url: 'frappe.client.get_value',
	makeParams(values) {
		return {
			doctype: 'LMS Course Progress',
			fieldname: ['status', 'scorm_content'],
			filters: {
				member: user.data?.name,
				lesson: chapter.doc.lessons[0].lesson,
				chapter: chapter.doc.name,
				course: chapter.doc?.course,
			},
		}
	},
	onSuccess(data) {
		readyToRender.value = true
	},
})

watch(readyToRender, async (ready) => {
	if (!ready || !chapter.doc?.is_h5p_package) return
	await nextTick()
	setupH5PPlayer()
})

const setupH5PPlayer = () => {
	if (!h5pContainer.value || isSuccessfullyCompleted.value) return

	// The constructor kicks off async loading of frame.bundle.js, which is what
	// actually defines window.H5P — the returned promise resolves once that's
	// loaded and the player is ready, so the externalDispatcher listener has to
	// be attached in .then(), not right after construction.
	new H5P(h5pContainer.value, {
		h5pJsonPath: chapter.doc.h5p_package_path,
		frameJs: h5pFrameJs,
		frameCss: h5pFrameCss,
	}).then(() => {
		// H5P content dispatches xAPI events for interactions/completion — record
		// the full statement for detailed tracking, and mirror "completed" with a
		// result into the same lesson-progress path SCORM content already uses, so
		// course-completion logic doesn't need to know which package type a lesson is.
		window.H5P.externalDispatcher.on('xAPI', (event) => {
			const statement = event.data?.statement
			if (!statement) return

			call('lms.lms.integrations.xapi.record_statement', {
				statement,
				course: props.courseName,
				lesson: chapter.doc.lessons[0].lesson,
			})

			if (statement.result?.completion && !isSuccessfullyCompleted.value) {
				isSuccessfullyCompleted.value = true
				saveProgress()
			}
		})
	})
}

const enrollStudent = () => {
	enrollment.insert.submit(
		{
			course: props.courseName,
			member: user.data?.name,
		},
		{
			onSuccess(data) {
				window.location.reload()
			},
		}
	)
}

const setupSCORMAPI = () => {
	window.API_1484_11 = {
		Initialize: () => 'true',
		Terminate: () => 'true',
		GetValue: (key) => {
			console.log(`GET: ${key}`)
			return getDataFromLMS(key)
		},
		SetValue: (key, value) => {
			console.log(`SET: ${key} to value: ${value}`)

			saveDataToLMS(key, value)
			return 'true'
		},
		Commit: () => 'true',
		GetLastError: () => '0',
		GetErrorString: () => '',
		GetDiagnostic: () => '',
	}
	window.API = {
		LMSInitialize: () => 'true',
		LMSFinish: () => 'true',
		LMSGetValue: (key) => {
			console.log(`GET: ${key}`)
			return getDataFromLMS(key)
		},
		LMSSetValue: (key, value) => {
			console.log(`SET: ${key} to value: ${value}`)
			saveDataToLMS(key, value)
			return 'true'
		},
		LMSCommit: () => 'true',
		LMSGetLastError: () => '0',
		LMSGetErrorString: () => '',
		LMSGetDiagnostic: () => '',
	}
}

const breadcrumbs = computed(() => {
	return [
		{
			label: __('Courses'),
			route: { name: 'Courses' },
		},
		{
			label: chapter.doc?.course_title,
			route: { name: 'CourseDetail', params: { courseName: props.courseName } },
		},
		{
			label: chapter.doc?.title,
		},
	]
})

usePageMeta(() => {
	return {
		title: chapter.doc?.title,
		icon: brand.favicon,
	}
})
</script>
