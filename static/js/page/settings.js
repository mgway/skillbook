define(
    [
        'component/settings_character_list',
    ],
    
    function(CharacterList) {

        function initialize() {
            CharacterList.attachTo("#character_list");
        }
        
        return initialize;
    }
);