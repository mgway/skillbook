define(
    [
        'flight/component',
        'hbs!templates/character_detail',
        'hbs/handlebars'
    ],
    function(defineComponent, template, handlebars) {
        return defineComponent(characterDetail);
        
        function characterDetail () {
            var lastRefreshTime;
            
            this.render = function(e, data) {
                // Don't constantly re-render
                if(lastRefreshTime != data.refreshTime) {
                    lastRefreshTime = data.refreshTime;
                    this.$node.html(template(data.character));
                }
            };
            
            this.hide = function(e, data) {
                this.$node.empty();
            };
            
            this.updateSP = function(e, data) {
                var template = handlebars.compile('{{commas skillpoints}}');
                this.$node.find('#skillpoints').html(template(data));
            };
           
            this.after('initialize', function() {
                this.on(document, 'dataCharacterDetailResponse', this.render);
                this.on(document, 'uiCharactersRequest', this.hide);
                this.on(document, 'uiSkillpointsUpdated', this.updateSP)
            });
       }
   }
);