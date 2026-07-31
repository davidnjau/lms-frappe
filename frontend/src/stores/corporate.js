import { defineStore } from 'pinia'
import { createListResource, createResource } from 'frappe-ui'

export const useCorporateStore = defineStore('corporate', () => {
	const summary = createResource({
		url: 'lms.lms.corporate.get_corporate_account_summary',
		auto: false,
	})

	const learnerProgress = createResource({
		url: 'lms.lms.corporate.get_corporate_learner_progress',
		auto: false,
	})

	const subscriptions = createListResource({
		doctype: 'LMS Subscription',
		fields: [
			'name',
			'plan_tier',
			'status',
			'seat_count',
			'billing_cycle',
			'renewal_date',
			'amount',
			'currency',
		],
		auto: false,
		orderBy: 'renewal_date desc',
	})

	return {
		summary,
		learnerProgress,
		subscriptions,
	}
})
