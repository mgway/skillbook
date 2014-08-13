define(
    [
        'component/settings/key_list',
    ],
    
    function(KeyList) {

        function initialize() {
            KeyList.attachTo("#character_list");
        }
        
        return initialize;
    }
);