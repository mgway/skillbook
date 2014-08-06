define(
    [
        'flight/lib/component',
        'hbs/handlebars'
    ],
    function(defineComponent, handlebars) {
        return defineComponent(planTitle);
        
        function planTitle() {
            
            this.defaultAttrs({
                clickSelector: '#pagetitle a',
            });
            
            this.updateTitleForList = function(e, data) {
                this.$node.text('Plans');
                
                $('title').text("skillbook | plans");
            };
            
            this.updateTitleForPlan = function(e, data) {
                var template = handlebars.compile('<a class="phony uk-link-muted">Plans</a> &raquo {{name}}');
                this.$node.html(template(data.plan));
                
                $('title').text("skillbook | " + data.plan.name);
            };
            
            this.updateTitleForPlans = function(e) {
                this.$node.html("Plans");
                this.trigger(document, 'uiPlansRequest');
            };
           
            this.after('initialize', function() {
                this.on(document, 'dataPlansResponse', this.updateTitleForList);
                this.on(document, 'dataPlanResponse', this.updateTitleForPlan);
                
                this.on(document, 'click', { 'clickSelector': this.updateTitleForPlans });
            });
       }
   }
);