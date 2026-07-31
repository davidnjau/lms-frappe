<template>
	<header
		class="sticky top-0 z-10 flex items-center justify-between border-b bg-surface-base px-3 py-2.5 sm:px-5"
	>
		<Breadcrumbs :items="breadcrumbs" />
	</header>

	<div v-if="summary.error" class="p-5 text-ink-red-4">
		{{ summary.error.messages?.[0] || summary.error.message }}
	</div>

	<div v-else-if="summary.data" class="pt-5 px-5 pb-10 mx-auto space-y-8">
		<div class="text-xl-semibold text-ink-gray-9">
			{{ props.corporateAccount }}
		</div>

		<div class="grid grid-cols-1 sm:grid-cols-3 gap-5">
			<div class="border rounded-md p-4">
				<div class="text-sm text-ink-gray-5">{{ __('Members') }}</div>
				<div class="text-xl-semibold text-ink-gray-9">
					{{ summary.data.member_count }}
				</div>
			</div>
			<div class="border rounded-md p-4">
				<div class="text-sm text-ink-gray-5">{{ __('Batches') }}</div>
				<div class="text-xl-semibold text-ink-gray-9">
					{{ summary.data.batch_count }}
				</div>
			</div>
			<div class="border rounded-md p-4">
				<div class="text-sm text-ink-gray-5">{{ __('Programs') }}</div>
				<div class="text-xl-semibold text-ink-gray-9">
					{{ summary.data.program_count }}
				</div>
			</div>
		</div>

		<div>
			<div class="text-lg-semibold text-ink-gray-9 mb-3">
				{{ __('Members') }}
			</div>
			<table class="w-full text-sm text-left border rounded-md">
				<thead class="text-ink-gray-5 border-b">
					<tr>
						<th class="p-2">{{ __('Name') }}</th>
						<th class="p-2">{{ __('Role') }}</th>
					</tr>
				</thead>
				<tbody>
					<tr
						v-for="member in summary.data.members"
						:key="member.member"
						class="border-b last:border-0"
					>
						<td class="p-2">{{ member.full_name || member.member }}</td>
						<td class="p-2">{{ member.role }}</td>
					</tr>
				</tbody>
			</table>
		</div>

		<div v-if="learnerProgress.data?.length">
			<div class="text-lg-semibold text-ink-gray-9 mb-3">
				{{ __('Learner Progress') }}
			</div>
			<table class="w-full text-sm text-left border rounded-md">
				<thead class="text-ink-gray-5 border-b">
					<tr>
						<th class="p-2">{{ __('Name') }}</th>
						<th class="p-2">{{ __('Average Progress') }}</th>
					</tr>
				</thead>
				<tbody>
					<tr
						v-for="member in learnerProgress.data"
						:key="member.member"
						class="border-b last:border-0"
					>
						<td class="p-2">{{ member.full_name || member.member }}</td>
						<td class="p-2">{{ member.average_progress }}%</td>
					</tr>
				</tbody>
			</table>
		</div>

		<div v-if="corporate.subscriptions.data?.length">
			<div class="text-lg-semibold text-ink-gray-9 mb-3">
				{{ __('Subscription') }}
			</div>
			<table class="w-full text-sm text-left border rounded-md">
				<thead class="text-ink-gray-5 border-b">
					<tr>
						<th class="p-2">{{ __('Plan') }}</th>
						<th class="p-2">{{ __('Seats') }}</th>
						<th class="p-2">{{ __('Billing Cycle') }}</th>
						<th class="p-2">{{ __('Renewal Date') }}</th>
						<th class="p-2">{{ __('Amount') }}</th>
						<th class="p-2">{{ __('Status') }}</th>
					</tr>
				</thead>
				<tbody>
					<tr
						v-for="subscription in corporate.subscriptions.data"
						:key="subscription.name"
						class="border-b last:border-0"
					>
						<td class="p-2">{{ subscription.plan_tier }}</td>
						<td class="p-2">{{ subscription.seat_count }}</td>
						<td class="p-2">{{ subscription.billing_cycle }}</td>
						<td class="p-2">{{ subscription.renewal_date }}</td>
						<td class="p-2">{{ subscription.amount }} {{ subscription.currency }}</td>
						<td class="p-2">
							<Badge :theme="subscription.status === 'Active' ? 'green' : 'gray'">
								{{ subscription.status }}
							</Badge>
						</td>
					</tr>
				</tbody>
			</table>
		</div>
	</div>
</template>
<script setup lang="ts">
import { onMounted } from 'vue'
import { Badge, Breadcrumbs, usePageMeta } from 'frappe-ui'
import { sessionStore } from '@/stores/session'
import { useCorporateStore } from '@/stores/corporate'

const { brand } = sessionStore()
const corporate = useCorporateStore()
const { summary, learnerProgress } = corporate

const props = defineProps<{
	corporateAccount: string
}>()

onMounted(() => {
	summary.submit({ corporate_account: props.corporateAccount })
	learnerProgress.submit({ corporate_account: props.corporateAccount })
	corporate.subscriptions.update({
		filters: { corporate_account: props.corporateAccount },
	})
	corporate.subscriptions.reload()
})

const breadcrumbs = [
	{
		label: props.corporateAccount,
		route: {
			name: 'CorporateDashboard',
			params: { corporateAccount: props.corporateAccount },
		},
	},
]

usePageMeta(() => {
	return {
		title: props.corporateAccount,
		icon: brand.favicon,
	}
})
</script>
