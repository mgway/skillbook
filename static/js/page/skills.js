define(function(require) {
                    
    function initialize() {
        require('data/characters').attachTo(document);
        require('component/character/refresh').attachTo(document);
        
        require('component/character/title').attachTo("#pagetitle");
        require('component/character/detail').attachTo("#character-detail");
        require('component/character/queue').attachTo("#character-queue");
        require('component/character/alert').attachTo("#character-flex");
        require('component/character/skills').attachTo("#character-flex");
        require('component/character/plan').attachTo("#character-flex");
        require('component/character/subnav').attachTo("#character-subnav");
        require('component/character/list').attachTo("#character-list");
        
        require('schedule').attachTo(document, {tickInterval: 10});
        require('history').attachTo(window, {
            routeBase: '/skills',
            routes: {'': 'uiCharactersRequest', 
                    '/character/{id}': 'uiCharacterRequest'
            }
        });
        
        var countdown = require('common/liveCountdown');
        setInterval(countdown, 5000);
    }
    
    return initialize;
});