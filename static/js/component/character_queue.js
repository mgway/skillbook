define(
    [
        'flight/component',
        'hbs!templates/character_queue',
        'moment'
    ],
    function(defineComponent, template, moment) {
        return defineComponent(characterQueue);
        
        function characterQueue() {

            this.render = function(e, data) {
                this.$node.html(template(data));
            };
            
            this.hide = function(e, data) {
                this.$node.empty();
                this.trigger('schedule-cancel', {
                    eventName: 'uiQueueRefresh'
                });
            };
           
            this.after('initialize', function() {
                this.on(document, 'dataCharacterQueueResponse', this.render);
                this.on(document, 'uiCharactersRequest', this.hide);
            });
        }
    }
);