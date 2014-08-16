'use strict';

define(
    [
        'flight/lib/component',
        'common/ajax',
        'moment',
        'underscore'
    ],
    function(defineComponent, ajax, moment, _) {
        return defineComponent(characters, ajax);
        
        function characters() {
            
            this.defaultAttrs({
                interval: 300000
            });

            this.fetchCharacters = function() {
                var characters = JSON.parse(localStorage.getItem('characters'));
                if (characters === null || moment() - moment(characters.refreshTime) > this.attr.interval) {
                    this.get({
                        xhr: {
                            url: '/api/character/'
                        },
                        events: {
                            done: 'dataCharactersResponse'
                        },
                        meta: {
                            key: 'characters'
                        }
                    });
                } else {
                    this.trigger('dataCharactersResponse', characters);
                }
            };
            
            this.saveCharacters = function(e, data) {
                data.refreshTime = moment();
                // Don't save an empty character list
                if (data.characters !== [])
                    localStorage.setItem('characters', JSON.stringify(data));
            };
		
            this.fetchCharacter = function(e, data) {
                var sheet = JSON.parse(localStorage.getItem('sheet_'+data.id));
                if (sheet === null || moment() - moment(sheet.refreshTime) > this.attr.interval) {
                    this.get({
                        xhr: {
                            url: '/api/character/' + data.id
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
                            url: '/api/character/' + data.id + "/queue"
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
                            url: '/api/character/' + data.id + "/skill"
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
                var groups = _.groupBy(data.skills, function(skill) { return skill.group_name });
                _.forEach(groups, function (group) { 
                    groupsList.push({
                        name: group[0].group_name,
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
                var finishedList = [];
                var now = moment.utc();
                var toSave = {};
                toSave.refreshTime = moment();
                toSave.queue = [];
                
                data.queue.forEach(function(skill) {
                    var start = moment.utc(skill.start_time);
                    var end = moment.utc(skill.end_time);
                    
                    if(start < now && end > now) {
                        // Skill is being trained now
                        skill.percent = Math.min(end - now, MS_PER_DAY) / 864000;
                        skill.current = true;
                    } else if (start > now) {
                        // Skill fits in 24 hour window, but isn't being trained now
                        skill.percent = Math.min(end - start, MS_PER_DAY) / 864000;
                    } else {
                        // Skill training completed; put in the completed queue 
                        // for estimated SP calculation
                        finishedList.push(skill);
                        return; 
                    }
                    
                    toSave.queue.push(skill);
                });
                
                // Shortcut for empty queue
                if (toSave.queue.length === 0) {
                    localStorage.setItem('queue_'+data.meta.characterId, JSON.stringify(toSave));
                    return;
                }
                
                var lastSkill = toSave.queue.slice(-1)[0];
                var lastSkillEnd = moment.utc(lastSkill.end_time);
                if (lastSkillEnd - now < MS_PER_DAY) { // 
                    toSave.queue.push({name: "Free Room", start_time: lastSkillEnd, 
                                    is_free_room: true, end_time: now.add('hours', 24) });
                } else {
                    toSave.has_multiple_skills = toSave.queue.length > 1;
                    toSave.end_time = lastSkillEnd;
                }
                
                toSave.finishedQueue = finishedList;
                toSave.current = toSave.queue[0];
                
                localStorage.setItem('queue_'+data.meta.characterId, JSON.stringify(toSave));
                
                this.trigger(document, 'dataCharacterQueueResponse', toSave);
            };
            
            this.fetchAlerts = function(e, data) {
                this.get({
                    xhr: {
                        url: '/api/character/' + data.id + "/alert"
                    },
                    events: {
                        done: 'dataCharacterAlertListResponse'
                    },
                    meta: {
                        key: 'data',
                        characterId: data.id
                    }
                });
            };
            
            this.updateAlerts = function(e, data) {
                this.post({
                    xhr: {
                        url: '/api/character/' + data.id + "/alert",
                        data: JSON.stringify(data.alerts)
                    },
                    events: {
                        done: 'dataCharacterAlertListResponse'
                    },
                    meta: {
                        key: 'data',
                        characterId: data.id,
                        updated: true
                    }
                });
            };
            
            this.fetchPlans = function(e, data) {
                this.get({
                    xhr: {
                        url: '/api/character/' + data.id + "/plan"
                    },
                    events: {
                        done: 'apiCharacterPlanResponse'
                    },
                    meta: {
                        key: 'plans',
                        characterId: data.id
                    }
                });
            };
            
            this.savePlans = function(e, data) {
                var toSave = {plans: data.plans, refreshTime: moment()};
                localStorage.setItem('plan_'+data.meta.characterId, JSON.stringify(toSave));
                
                this.trigger(document, 'dataCharacterPlanListResponse', toSave);
            };

            this.after('initialize', function () {
                this.on(document, 'uiCharactersRequest', this.fetchCharacters);
                this.on(document, 'uiCharacterRequest', this.fetchCharacter);
                this.on(document, 'uiCharacterRefresh', this.fetchCharacter);
                this.on(document, 'uiNeedsAlertList', this.fetchAlerts);
                this.on(document, 'uiNeedsPlanList', this.fetchPlans);
                this.on(document, 'uiSaveAlertList', this.updateAlerts);

                this.on('dataCharactersResponse', this.saveCharacters);
                this.on('apiCharacterDetailResponse', this.saveSheet);
                this.on('apiCharacterQueueResponse', this.saveQueue);
                this.on('apiCharacterSkillsResponse', this.saveSkills);
                this.on('apiCharacterPlanResponse', this.savePlans);
            });
        }
    }
);