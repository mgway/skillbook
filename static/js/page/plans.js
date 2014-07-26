define(
    [
        'component/plan_title',
        'data/plans',
        'schedule',
        'history',
    ],
    
    function(PlanTitle, PlanStore, Schedule, 
                History) {

        function initialize() {
            PlanStore.attachTo(document);

            PlanTitle.attachTo("#pagetitle");
            
            Schedule.attachTo(document, {tickInterval: 10});
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