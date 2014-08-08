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
            
            this.switchPage = function(e, data) {
                var el = $(data.el);
                var parentUl = el.parent().parent();
                var characterId = parentUl.data('character');
                var id = el.attr('id').split('_')[1];
                
                parentUl.children().removeClass('uk-active');
                el.parent().addClass('uk-active');
                this.trigger(document, 'uiSwitchCharacterTab', {page: id, id: characterId});
            };
           
            this.after('initialize', function() {
                this.on(document, 'uiCharacterRequest', this.render);
                this.on(document, 'uiCharactersRequest', this.hide);
                
                this.on('click', { 'clickSelector': this.switchPage });
            });
       }
   }
);