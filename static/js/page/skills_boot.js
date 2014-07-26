require(['../boot'], 
    function (common) {
        require(
        [  
            'flight/lib/debug'
        ],
        function(debug) {
            debug.enable(true);
            require(['page/skills'], function(initialize) {
                initialize();
            });
        });
    }
);