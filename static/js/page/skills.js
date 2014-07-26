define(
    [
        'component/character_title',
        'component/character_list',
        'component/character_detail',
        'component/character_queue',
        'component/character_skills',
        'component/character_refresh',
        'data/characters',
        'schedule',
        'history',
        'common/liveCountdown'
    ],
    
    function(CharacterTitle, CharacterList, CharacterDetail, CharacterQueue, 
                CharacterSkills, CharacterRefresh, CharacterStore, Schedule, 
                History, countdown) {

        function initialize() {
            CharacterStore.attachTo(document);
            CharacterRefresh.attachTo(document);
            
            CharacterTitle.attachTo("#pagetitle");
            CharacterDetail.attachTo("#character_detail");
            CharacterQueue.attachTo("#character_queue");
            CharacterSkills.attachTo("#character_skills");
            CharacterList.attachTo("#character_list");
            
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