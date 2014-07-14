'use strict';

define(
    [
        'flight/component',
        'common/ajax',
        'moment',
        'underscore'
    ],
    function(defineComponent, ajax, moment, _) {
        return defineComponent(todos, ajax);
        
        function todos() {
            
            this.defaultAttrs({
                interval: 300000
            });

            this.fetchCharacters = function() {
                var refreshTime = localStorage.getItem('characters_refresh_time');
                if (refreshTime === null || moment() - moment(refreshTime) > this.attr.interval) {
                    this.get({
                        xhr: {
                            url: '/api/characters/'
                        },
                        events: {
                            done: 'dataCharactersResponse'
                        },
                        meta: {
                            key: 'characters'
                        }
                    });
                } else {
                    var characters = JSON.parse(localStorage.getItem('characters'));
                    this.trigger('dataCharactersResponse', {characters: characters});
                }
            };
            
            this.saveCharacters = function(e, data) {
                localStorage.setItem('characters', JSON.stringify(data.characters));
                localStorage.setItem('characters_refresh_time', moment());
            };
		
            this.fetchCharacter = function(e, data) {
                var sheet = JSON.parse(localStorage.getItem('sheet_'+data.id));
                if (sheet === null || moment() - moment(sheet.refreshTime) > this.attr.interval) {
                    this.get({
                        xhr: {
                            url: '/api/sheet/' + data.id
                        },
                        events: {
                            done: 'apiCharacterDetailResponse'
                        },
                        meta: {
                            key: 'character',
                            characterId: data.id
                        }
                    });
                } else {
                    this.trigger(document, 'dataCharacterDetailResponse', sheet);
                }
                
                var queue = JSON.parse(localStorage.getItem('queue_'+data.id));
                if (queue === null || moment() - moment(queue.refreshTime) > this.attr.interval) {
                    this.get({
                        xhr: {
                            url: '/api/queue/' + data.id
                        },
                        events: {
                            done: 'apiCharacterQueueResponse'
                        },
                        meta: {
                            key: 'queue',
                            characterId: data.id
                        }
                    });
                } else {
                    this.trigger(document, 'dataCharacterQueueResponse', queue);
                }
                
                var skills = JSON.parse(localStorage.getItem('skills_'+data.id));
                if (skills === null || moment() - moment(skills.refreshTime) > this.attr.interval) {
                    this.get({
                        xhr: {
                            url: '/api/skills/' + data.id
                        },
                        events: {
                            done: 'apiCharacterSkillsResponse'
                        },
                        meta: {
                            key: 'skills',
                            characterId: data.id
                        }
                    });
                } else {
                    this.trigger(document, 'dataCharacterSkillsResponse', skills);
                }
            };
            
            this.saveSheet = function(e, data) {
                var toSave = {character: data.character, refreshTime: moment()};
                localStorage.setItem('sheet_'+data.meta.characterId, JSON.stringify(toSave));
                
                this.trigger(document, 'dataCharacterDetailResponse', toSave);
            };
            
            this.saveSkills = function(e, data) {
                var groupsList = [];
                var groups = _.groupBy(data.skills, function(skill) { return skill.groupname });
                _.forEach(groups, function (group) { 
                    groupsList.push({
                        name: group[0].groupname,
                        skillpoints: _.reduce(group, function(memo, skill) { return skill.skillpoints + memo }, 0),
                        count: group.length,
                        skills: _.sortBy(group, function(skill) { return skill.name }) 
                    });
                });
                groupsList = _.sortBy(groupsList, function(group) { return group.name; });
                
                var toSave = {groups: groupsList, refreshTime: moment()};
                localStorage.setItem('skills_'+data.meta.characterId, JSON.stringify(toSave));
                
                this.trigger(document, 'dataCharacterSkillsResponse', toSave);
            };
            
            this.saveQueue = function(e, data) {
                var MS_PER_DAY = 86400000; // 24*60*60*1000
                var queueList = [];
                var now = moment.utc();
                var toSave = {};
                toSave.refreshTime = moment();
                
                data.queue.forEach(function(skill) {
                    var start = moment.utc(skill.starttime);
                    var end = moment.utc(skill.endtime);
                    
                    if(start < now && end > now) {
                        // Skill is being trained now
                        skill.percent = Math.min(end - now, MS_PER_DAY) / 864000;
                        skill.current = true;
                    } else if (start > now) {
                        // Skill fits in 24 hour window, but isn't being trained now
                        skill.percent = Math.min(end - start, MS_PER_DAY) / 864000;
                    } else {
                        return; // Skill training completed
                    }
                    
                    queueList.push(skill);
                });
                
                // Shortcut for empty queue
                if (queueList.length === 0) {
                    localStorage.setItem('queue_'+data.meta.characterId, JSON.stringify(toSave));
                    return;
                }
                
                var last_skill = queueList.slice(-1)[0];
                var endTime = moment.utc(last_skill.endtime);
                if (endTime - now < MS_PER_DAY) { // 
                    queueList.push({name: "Free Room", starttime: endTime, 
                                    is_free_room: true, endtime: now.add('hours', 24) });
                } else {
                    toSave.has_multiple_skills = queueList.length > 1;
                    toSave.end_time = last_skill.endtime;
                }
                
                toSave.queue = queueList;
                toSave.current = queueList[0];
                
                localStorage.setItem('queue_'+data.meta.characterId, JSON.stringify(toSave));
                
                this.trigger(document, 'dataCharacterQueueResponse', toSave);
            };

            this.after('initialize', function () {
                this.on(document, 'uiCharactersRequest', this.fetchCharacters);
                this.on(document, 'uiCharacterRequest', this.fetchCharacter);
                this.on(document, 'uiCharacterRefresh', this.fetchCharacter);
                
                this.on('dataCharactersResponse', this.saveCharacters);
                this.on('apiCharacterDetailResponse', this.saveSheet);
                this.on('apiCharacterQueueResponse', this.saveQueue);
                this.on('apiCharacterSkillsResponse', this.saveSkills);
            });
        }
    }
);