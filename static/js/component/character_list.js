define(
    [
        'flight/component',
        'hbs!templates/character_list'
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
            
            this.requestDisplayCharacter = function(e, data) {
                var id = $(data.el).attr('id').split('_')[1];
                this.trigger(document, 'uiCharacterRequest', {id: id});
            };
           
            this.after('initialize', function() {
                this.on(document, 'dataCharactersResponse', this.render);
                this.on(document, 'uiCharacterRequest', this.hide);

                this.on('click', { 'clickSelector': this.requestDisplayCharacter });
                
                //this.trigger(document, 'uiCharactersRequest');
            });
       }
   }
);