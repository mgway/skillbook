define(
    [
        'flight/lib/component',
        'hbs!templates/character/plan',
    ],
    function(defineComponent, template) {
        return defineComponent(characterPlan);
        
        function characterPlan () {
            
            this.defaultAttrs({
                rowClickSelector: '.plan-row',
            });
            
            this.render = function(e, data) {
                console.log(data);
                this.$node.html(template(data));
            };
            
            this.switchTab = function(e, data) {
                if (data.page == 'plans') {
                    this.trigger(document, 'uiNeedsPlanList', {id: data.id});
                    this.characterId = data.id;
                }
            };
            
            this.openPlanWindow = function(e, data) {
                var el = $(e.target);
                
                window.open("/plans/" + el.parent('tr').data('planid'), '_blank');
            };
           
            this.after('initialize', function() {
                this.on(document, 'dataCharacterPlanListResponse', this.render);
                this.on(document, 'uiSwitchCharacterTab', this.switchTab);
                this.on('click', { 'rowClickSelector': this.openPlanWindow });
            });
       }
   }
);