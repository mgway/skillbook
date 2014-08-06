define(
    [
        'flight/lib/component',
        'hbs/handlebars'
    ],
    function(defineComponent, handlebars) {
        return defineComponent(characterTitle);
        
        function characterTitle() {
            
            this.defaultAttrs({
                clickSelector: '#pagetitle a',
            });
            
            this.updateTitleForList = function(e, data) {
                this.$node.text('Characters');
                
                $('title').text("skillbook | characters");
            };
            
            this.updateTitleForCharacter = function(e, data) {
                var template = handlebars.compile('<a class="phony uk-link-muted">Characters</a> &raquo {{name}}');
                this.$node.html(template(data.character));
                
                $('title').text("skillbook | " + data.character.name);
            };
            
            this.updateTitleForCharacters = function(e) {
                this.$node.html("Characters");
                this.trigger(document, 'uiCharactersRequest');
            };
           
            this.after('initialize', function() {
                this.on(document, 'dataCharactersResponse', this.updateTitleForList);
                this.on(document, 'dataCharacterDetailResponse', this.updateTitleForCharacter);
                
                this.on(document, 'click', { 'clickSelector': this.updateTitleForCharacters });
            });
       }
   }
);