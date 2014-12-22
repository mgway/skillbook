define(function(require) {
    function initialize() {
        
        require('data/plans').attachTo(document);
        require('data/static').attachTo(document);
        
        require('component/plan/title').attachTo("#pagetitle");
        require('component/plan/list').attachTo("#plan-list");
        require('component/plan/subnav').attachTo("#plan-subnav");
        require('component/plan/entries').attachTo("#plan-flex");
        
        require('history').attachTo(window, {
            routeBase: '/plans',
            routes: {'': 'uiNeedsPlanList', 
                    '/plan/{id}': 'uiNeedsPlanEntries'
            }
        });
    }
    
    return initialize;
});
