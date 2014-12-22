'use strict';

define(
    [
        'flight/lib/component',
        'common/ajax',
        'moment',
        'underscore'
    ],
    function(defineComponent, ajax, moment, _) {
        return defineComponent(plans, ajax);
        
        function plans() {
            
            this.defaultAttrs({
                interval: 300000
            });

            this.fetchPlans = function() {
                var plans = JSON.parse(localStorage.getItem('plans'));
                if (plans === null || moment() - moment(plans.refreshTime) > this.attr.interval) {
                    this.get({
                        xhr: {
                            url: '/api/plan/'
                        },
                        events: {
                            done: 'apiPlansResponse'
                        },
                        meta: {
                            key: 'plans'
                        }
                    });
                } else {
                    this.trigger('dataPlansResponse', plans);
                }
            };
            
            this.savePlans = function(e, data) {
                data.refreshTime = moment();
                // Don't save an empty plan list
                if (data.plans !== [])
                    localStorage.setItem('plans', JSON.stringify(data));
                this.trigger('dataPlansResponse', data);
            };
		
            this.fetchPlan = function(e, data) {
                var plan = JSON.parse(localStorage.getItem('plan_'+data.id));
                if (plan === null || moment() - moment(plan.refreshTime) > this.attr.interval) {
                    this.get({
                        xhr: {
                            url: '/api/plan/' + data.id
                        },
                        events: {
                            done: 'apiPlanResponse'
                        },
                        meta: {
                            key: 'plan',
                            planId: data.id
                        }
                    });
                } else {
                    this.trigger(document, 'dataPlanEntries', plan);
                }
            };
            
            this.savePlan = function(e, data) {
                data.refreshTime = moment();
                localStorage.setItem('plan_'+data.meta.planId, JSON.stringify(data));
                
                this.trigger(document, 'dataPlanResponse', data);
            };
            
            this.addPlan = function(e, data) {
                this.post({
                    xhr: {
                        data: data,
                        url: '/api/plan/'
                    },
                    events: {
                        done: 'apiPlansResponse'
                    },
                    meta: {
                        key: 'plans',
                    }
                });
            };
            
            this.addPlanEntry = function(e, data) {
                this.post({
                    xhr: {
                        url: '/api/plan/' + data.id
                    },
                    events: {
                        done: 'apiPlanResponse'
                    },
                    meta: {
                        key: 'plan',
                        planId: data.id
                    }
                });
            };
            
            this.after('initialize', function () {
                this.on(document, 'uiNeedsPlanList', this.fetchPlans);
                this.on(document, 'uiNeedsPlanEntries', this.fetchPlan);
                this.on(document, 'uiAddPlanRequest', this.addPlan);
                this.on(document, 'uiAddPlanEntryRequest', this.addPlanEntry);
                
                this.on('apiPlansResponse', this.savePlans);
                this.on('apiPlanResponse', this.savePlan);
            });
        }
    }
);