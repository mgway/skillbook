define('templates/helpers/timeDifference', ['hbs/handlebars', 'common/preciseMoment'], 
    function(Handlebars, moment) {
        function timeDifference(first, second, options) {
            var firstMoment, secondMoment;
            
            // Account for only one argument when fromNow=true
            options = options === undefined? second : options;
            
            if (options.hash.fromNow) {
                firstMoment = moment.utc();
                secondMoment = moment.utc(first);
            } else {
                firstMoment = moment.utc(first);
                secondMoment = moment.utc(second);
            }
            
            var now = moment.utc();
            
            if (firstMoment < now)
                return now.preciseDiff(secondMoment);
            else
                return firstMoment.preciseDiff(secondMoment);
        }
        
        Handlebars.registerHelper('timeDifference', timeDifference);
        return timeDifference;
    }
);