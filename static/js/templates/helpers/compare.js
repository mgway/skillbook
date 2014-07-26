define('templates/helpers/compare', ['hbs/handlebars'], 
    function(Handlebars) {
        function compare(lvalue, rvalue, options) {
            if (arguments.length < 3)
                throw new Error("Compare block needs 2 parameters");
                
            var operator = options.hash.op || "==";
            var operators = {
                '==':       function(l,r) { return l == r; },
                '===':      function(l,r) { return l === r; },
                '!=':       function(l,r) { return l != r; },
                '<':        function(l,r) { return l < r; },
                '>':        function(l,r) { return l > r; },
                '<=':       function(l,r) { return l <= r; },
                '>=':       function(l,r) { return l >= r; },
                'typeof':   function(l,r) { return typeof l == r; }
            };
        
            if (!operators[operator])
                throw new Error("Unknown operator: " + operator);

            var result = operators[operator](lvalue,rvalue);

            if( result ) {
                return options.fn(this);
            } else {
                return options.inverse(this);
            }
        }
        Handlebars.registerHelper('compare', compare);
        return compare;
    }
);