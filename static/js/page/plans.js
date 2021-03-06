define(
    [
        'component/plan/title',
        'component/plan/list',
        'data/plans',
        'schedule',
        'history',
    ],
    
    function(PlanTitle, PlanList, PlanStore, Schedule, History) {

        function initialize() {
            PlanStore.attachTo(document);

            PlanTitle.attachTo("#pagetitle");
            PlanList.attachTo("#plan_list");
            
            History.attachTo(window, {
                routeBase: '/plans',
                routes: {'': 'uiPlansRequest', 
                        '/plan/{id}': 'uiPlanRequest'
                }
            });
        }
        
        return initialize;
    }
);