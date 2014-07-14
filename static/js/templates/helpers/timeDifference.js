define('templates/helpers/timeDifference', ['hbs/handlebars', 'common/preciseMoment'], 
    function(Handlebars, moment) {
        function timeDifference(first, second, options) {
            var firstMoment;
            
            if (first == "now") {
                firstMoment = moment.utc();
            } else {
                firstMoment = moment.utc(first);
            }
            
            var secondMoment = moment.utc(second);
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