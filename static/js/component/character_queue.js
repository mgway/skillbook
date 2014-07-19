define(
    [
        'flight/lib/component',
        'hbs!templates/character_queue',
        'moment'
    ],
    function(defineComponent, template, moment) {
        return defineComponent(characterQueue);
        
        function characterQueue() {

            this.render = function(e, data) {
                this.$node.html(template(data));
                
                var that = this;
                data.queue.forEach(function(skill) {
                    that.trigger(document, 'uiSetSkillInTraining', skill);
                });
            };
            
            this.hide = function(e, data) {
                this.$node.empty();
            };
           
            this.after('initialize', function() {
                this.on(document, 'dataCharacterQueueResponse', this.render);
                this.on(document, 'uiCharactersRequest', this.hide);
            });
        }
    }
);