define(
    [
        'flight/lib/component',
        'hbs!templates/character_subnav'
    ],
    function(defineComponent, template) {
        return defineComponent(characterSubnav);
        
        function characterSubnav () {
            
            this.defaultAttrs({
                clickSelector: '.uk-subnav a',
            });
            
            this.render = function(e, data) {
                this.$node.html(template(data));
            };
            
            this.hide = function(e, data) {
                this.$node.empty();
            };
            
            this.requestPage = function(e, data) {
                alert('soon (tm)');
            };
           
            this.after('initialize', function() {
                this.on(document, 'uiCharacterRequest', this.render);
                this.on(document, 'uiCharactersRequest', this.hide);
                
                this.on('click', { 'clickSelector': this.requestPage });
            });
       }
   }
);