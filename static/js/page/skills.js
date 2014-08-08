define(
    [
        'component/character/title',
        'component/character/list',
        'component/character/detail',
        'component/character/queue',
        'component/character/skills',
        'component/character/subnav',
        'component/character/alert',
        'component/character/refresh',
        'data/characters',
        'schedule',
        'history',
        'common/liveCountdown'
    ],
    
    function(CharacterTitle, CharacterList, CharacterDetail, CharacterQueue, 
                CharacterSkills, CharacterSubnav, CharacterAlert, CharacterRefresh, CharacterStore, Schedule, 
                History, countdown) {

        function initialize() {
            CharacterStore.attachTo(document);
            CharacterRefresh.attachTo(document);
            
            CharacterTitle.attachTo("#pagetitle");
            CharacterDetail.attachTo("#character-detail");
            CharacterQueue.attachTo("#character-queue");
            CharacterAlert.attachTo("#character-flex");
            CharacterSkills.attachTo("#character-flex");
            CharacterSubnav.attachTo("#character-subnav");
            CharacterList.attachTo("#character-list");
            
            Schedule.attachTo(document, {tickInterval: 10});
            History.attachTo(window, {
                routeBase: '/skills',
                routes: {'': 'uiCharactersRequest', 
                        '/character/{id}': 'uiCharacterRequest'
                }
            });
            
            setInterval(countdown, 5000);
        }
        
        return initialize;
    }
);