define(
    [
        'flight/component',
        'underscore',
        'hbs!templates/character_skills'
    ],
    function(defineComponent, _, template) {
        return defineComponent(characterSkills);
        
        function characterSkills() {

            var lastRefreshTime;
            
            this.defaultAttrs({
                clickSelector: 'thead',
            });
            
            this.render = function(e, data) {
                // Don't constantly re-render
                if(lastRefreshTime != data.refreshTime || this.$node.html() === "") {
                    lastRefreshTime = data.refreshTime;
                    this.$node.html(template(data));
                }
            };
            
            this.hide = function(e, data) {
                this.$node.empty();
            };
            
            this.hideGroup = function(e) {
                $(e.target).parents('table').find('tbody').toggle();
            };
            
            this.setTraining = function(e, data) {
                var id = '#skill_' + data.typeid;
                var row = this.$node.find(id);
                row.css('background-color', 'rgba(94, 162, 230, 0.29)');
                var img = row.find('img');
                var src = '/static/img/skill' + img.data('level') + 'q' + data.level + '.png';
                img.attr('src', src);
            };
            
            this.setTrainingComplete = function(e, data) {
                var id = '#skill_' + data.typeid;
                var row = this.$node.find(id);
                var img = row.find('img');
                var src = '/static/img/skill' + data.level + '.png';
                img.attr('src', src);
            };
           
            this.after('initialize', function() {
                this.on(document, 'dataCharacterSkillsResponse', this.render);
                this.on(document, 'uiCharactersRequest', this.hide);
                this.on(document, 'uiSetSkillInTraining', this.setTraining);

                this.on(document, 'click', { 'clickSelector': this.hideGroup });
            });
       }
   }
);