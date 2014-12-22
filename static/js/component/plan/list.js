define(
    [
        'flight/lib/component',
        'hbs!templates/plan/list'
    ],
    function(defineComponent, template) {
        return defineComponent(characterList);
        
        function characterList () {
            
            this.defaultAttrs({
                clickSelector: '.uk-comment',
            });
            
            this.render = function(e, data) {
                this.$node.html(template(data));
            };
            
            this.hide = function(e, data) {
                this.$node.empty();
            };
            
            this.requestDisplayPlan = function(e, data) {
                var id = $(data.el).attr('id').split('_')[1];
                this.trigger(document, 'uiNeedsPlanEntries', {id: id});
            };
           
            this.after('initialize', function() {
                this.on(document, 'dataPlansResponse', this.render);
                this.on(document, 'uiNeedsPlanEntries', this.hide);
                
                this.on('click', { 'clickSelector': this.requestDisplayPlan });
            });
       }
   }
);