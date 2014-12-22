define(
    [
        'flight/lib/component',
        'hbs!templates/plan/entries'
    ],
    function(defineComponent, template) {
        return defineComponent(planEntries);
        
        function planEntries() {

            var isVisible = true;
            
            this.render = function(e, data) {
                if(!isVisible)
                    return;
                
                this.$node.html(template(data.plan));
            };
            
            this.hide = function(e, data) {
                this.$node.empty();
            };
            
            this.switchTab = function(e, data) {
                if(data.page == 'entries') {
                    isVisible = true;
                    this.trigger(document, 'uiNeedsPlanEntries', data);
                } else {
                    isVisible = false;
                }
            };
           
            this.after('initialize', function() {
                this.on(document, 'dataPlanEntries', this.render);
                this.on(document, 'uiNeedsPlanList', this.hide);
                this.on(document, 'uiSwitchPlanTab', this.switchTab);
            });
       }
   }
);