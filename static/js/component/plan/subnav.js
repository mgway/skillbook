define(
    [
        'flight/lib/component',
        'hbs!templates/plan/subnav'
    ],
    function(defineComponent, template) {
        return defineComponent(planSubnav);
        
        function planSubnav() {
            
            this.defaultAttrs({
                clickSelector: '.uk-subnav a',
            });
            
            this.render = function(e, data) {
                this.$node.html(template(data));
            };
            
            this.hide = function(e, data) {
                this.$node.empty();
            };
            
            this.switchPage = function(e, data) {
                var el = $(data.el);
                var parentUl = el.parent().parent();
                var planId = parentUl.data('plan');
                var id = el.attr('id').split('-')[1];
                
                parentUl.children().removeClass('uk-active');
                el.parent().addClass('uk-active');
                this.trigger(document, 'uiSwitchPlanTab', {page: id, id: planId});
            };
           
            this.after('initialize', function() {
                this.on(document, 'uiNeedsPlanEntries', this.render);
                this.on(document, 'uiNeedsPlanList', this.hide);
                
                this.on('click', { 'clickSelector': this.switchPage });
            });
       }
   }
);