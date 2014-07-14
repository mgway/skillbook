define(
    [
        'flight/component',
        'hbs!templates/character_detail',
        'hbs/handlebars'
    ],
    function(defineComponent, template, handlebars) {
        return defineComponent(characterDetail);
        
        function characterDetail () {
		
            this.render = function(e, data) {
                this.$node.html(template(data.character));
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