define(
    [
        'component/settings/key_list',
        'component/settings/mail'
    ],
    
    function(KeyList, Mail) {

        function initialize() {
            KeyList.attachTo("#character_list");
            Mail.attachTo("#mail");
        }
        
        return initialize;
    }
);