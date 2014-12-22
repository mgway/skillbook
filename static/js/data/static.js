'use strict';

define(
    [
        'flight/lib/component',
        'common/ajax',
        'moment',
        'underscore', 
        'depot'
    ],
    function(defineComponent, ajax, moment, _, depot) {
        return defineComponent(staticStore, ajax);
        
        function staticStore() {
            
            var skills = depot('skills');
            var items = depot('items');
            
            this.defaultAttrs({
                interval: 300000,
            });

            this.fetchSkills = function() {
                if (skills.size() === 0) {
                    this.get({
                        xhr: {
                            url: '/api/static/skill/'
                        },
                        events: {
                            done: 'apiStaticSkillsResponse'
                        },
                        meta: {
                            key: 'skills'
                        }
                    });
                } else {
                    this.trigger('dataStaticSkillsResponse', skills.all());
                }
            };
            
            this.saveSkills = function(e, data) {
                data.skills.each(function(i, el) {
                    el['isAGroup'] = false;
                    skills.save(el);
                });
                
                var groupsList = [];
                var groups = _.groupBy(data.skills, function(skill) { return skill.group_name });
                _.forEach(groups, function (group) { 
                    groupsList.push({
                        name: group[0].group_name,
                        count: group.length,
                        skills: _.sortBy(group, function(skill) { return skill.name }) 
                    });
                });
                groupsList = _.sortBy(groupsList, function(group) { return group.name; });
                data.skills.each(function(i, el) {
                    el['isAGroup'] = true;
                    skills.save(el);
                });
                
                this.trigger('dataStaticSkillsResponse', skills.find({'isAGroup': false}));
            };

            this.after('initialize', function () {
                this.on(document, 'uiNeedsStaticSkillList', this.fetchSkills);
                
                this.on('apiStaticSkillsResponse', this.saveSkills);
            });
        }
    }
);