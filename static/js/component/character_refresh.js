define(
    [
        'flight/component',
    ],
    function(defineComponent) {
        return defineComponent(characterQueue);
        
        function characterQueue() {

            this.startRefresh = function(e, data) {
                this.trigger('schedule-task', {
                    eventName: 'uiCharacterRefresh',
                    data: data,
                    period: 20,
                    immediate: false
                });
            };

            this.cancelRefresh = function(e, data) {
                this.trigger('schedule-cancel', {
                    eventName: 'uiQueueRefresh'
                });
            };
           
            this.after('initialize', function() {
                this.on(document, 'uiCharacterRequest', this.startRefresh);
                this.on(document, 'uiCharactersRequest', this.cancelRefresh);
            });
        }
    }
);