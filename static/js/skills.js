window.addEvent('domready', function() {
	skillbook.cache = {}
	skillbook.static = {}
	var clocks = [];
    var total_sp = 0;


	if(window.location.hash) {
		split = window.location.hash.split('/');
		if(split[0] == '#character') {
			show_character(split[1]);
		} else {
			list_characters();	
		}
	} else {
		list_characters();
	}


	function list_characters() {
		window.location.hash = 'characters';

		// Clean up
		$('pagegrid').empty();
		$$('table').dispose();
		$('pagetitle').set('text', 'Characters');
		clocks.each(function(idx) {clearInterval(idx)});

		skillbook.api('characters', function(characters) {
			var grid = $('pagegrid');
			characters.each(function(char) {
				grid.grab(character_row(char));
			});

			function character_row(char) {
				var row = new Element('div', {'class': 'uk-width-1-1 uk-width-medium-1-1 uk-width-large-1-2', 'style':'padding-bottom: 10px'});
				var article = new Element('article', {'class': 'uk-comment'});
				var header = new Element('header', {'class': 'uk-comment-header'});
				var data = char['corporationname'] + "<br />" + skillbook.format_isk(char['balance']);
				if(char['training_end']) {
					var rowid = "timer_" + char['characterid'];
					data += "<br />Queue finishes in <span id='"+rowid+"'></span>";
					clocks.push(setInterval(function(){update_timer(rowid, char['training_end'])}, 500));
				}
				header.adopt(
					skillbook.portrait(char['characterid'], char['name'], 'Character', 128, 'uk-comment-avatar'), 
					new Element('h4', {'html': char['name'], 'class': 'uk-comment-title'}),
					new Element('div', {'html': data, 'class': 'uk-comment-meta'})
				);
				article.grab(header);
				row.grab(article);
				row.addEvent('click', function(e) {
					show_character(char['characterid']);
				});
				return row;
			}

			function update_timer(id, endTime) {
				// This is rough, but we use moment and moment-precise to display the queue end time 
				// (provided by the api as a UTC timestamp) as months/days/hours/minutes
				element = $(id);
				var offset = new Date().getTimezoneOffset();
				var endTime = moment(endTime).subtract('minutes', offset);
				var delta = endTime - new Date().getTime();
				element.title = endTime.format('LLLL');
				element.innerText = endTime.preciseDiff(moment())
				if(delta < 86400000) {
					element.setStyle('color', 'red');
					if(delta < 0) {
						element.innerText = "0m";
					}
				}
			}
		});
	}

	function show_character(id) {
		// First, kill our timers
		clocks.each(function(idx) {clearInterval(idx)});

		// Push the character id onto the hash for bookmarking purposes (or something)
		window.location.hash = 'character/' + id;
		$('pagegrid').empty();

		// Check the cache first
		if(skillbook.cache[id] == undefined) {
			// Fetch the list of skills (static)
			skillbook.api('static/skills', function(skills) {
				skillbook.static = skills

				skillbook.cache[id] = {}
				skillbook.api("sheet/" + id, function(sheet) {
					skillbook.cache[id] = sheet;
					display_sheet();
				});
				skillbook.api("skills/" + id, function(skills) {
					// Join (hooray client side join) static skill data with this character's SP/level
					skills.each(function(skill) {
						_.extend(skill, skillbook.static[skill.typeid]);
					});
					skillbook.cache[id].skills = skills;
					display_skills();
				});
				skillbook.api("queue/" + id, function(queue) {
					queue.each(function(skill) {
						_.extend(skill, skillbook.static[skill.typeid]);
					});
					skillbook.cache[id].queue = queue;
					display_queue();
				});
			});
		} else {
			display_sheet();
			display_skills();
			display_queue();
		}
		//clocks.push(setInterval(function(){display_queue()}, 5000));

		function display_sheet() {
			var sheet = skillbook.cache[id];

			// Set up our header
			var list_chars = new Element('a', {'text': 'Characters', 'style': 'cursor: pointer', 'class': 'uk-link-muted'});
			var trailer = new Element('span', {'html': ' &raquo; ' + sheet.name});
			list_chars.addEvent('click', list_characters);
			$('pagetitle').empty().adopt(list_chars, trailer);

			// Set up the character brief
			var panel = new Element('div', {'class': 'uk-width-1-1 uk-hidden-small'});
			var list = new Element('dl', {'class': 'uk-description-list uk-description-list-horizontal'});
            var massaged = {'Bio': sheet['bio'], 'Balance': skillbook.format_isk(sheet['balance']),
                'Birthday': moment(sheet['birthday']).subtract('minutes', new Date().getTimezoneOffset()).format('LLL'), 
                'Corporation': sheet['corporationname'], 'Skillpoints': 100, 
                'Clone': skillbook.format_number(sheet['clonesp']) + " (" + sheet['clonegrade'] + ")"
            }

            _.each(massaged, function(value, key) {
				list.adopt(new Element('dt', {'html': key}), new Element('dd', {'html': value, 'id': 'sheet_'+key}));
            });

			panel.adopt(
				skillbook.portrait(sheet['characterid'], sheet['name'], 'Character', 128, 'uk-comment-avatar'), 
				list
			);
			var grid = $('pagegrid');
			grid.grab(panel);
		}

		function display_skills() {
			var groups = _.groupBy(skillbook.cache[id].skills, function(skill){ return skill.groupname });
			var frame = $('frame');
			_.sortBy(groups, function(group) { return group[0].groupname }).each(function(skills, key) { 
				frame.grab(skill_category(skills, key));
			});

            $('sheet_Skillpoints').set('html', skillbook.format_number(total_sp));
		}

		function display_queue() {
			var queue = skillbook.cache[id].queue;
			var panel = $('skillqueue');
			if (panel == undefined) {
				panel = new Element('div', {'class': 'uk-width-1-1 uk-panel', 'id':'skillqueue', 'style': 'padding-top: 10px'});
			} else {
				panel.empty();
			}
			panel.adopt(new Element('h4', {'class': 'uk-panel-title', 'text': 'Queue'}));
			var endTime = skillbook.to_localtime(queue.getLast().endtime);
			panel.adopt(new Element('span', {'text': endTime.preciseDiff(moment())}));
			panel.adopt(new Element('span', {'class': 'uk-float-right', 'text': endTime.format('LLLL')}));

			var table = new Element('table', {'style': 'width: 100%', 'id': 'queue'});
			var row = new Element('tr');

			var current_skill; 
			queue.each(function(skill) {
				var start = skillbook.to_localtime(skill.starttime);
				var end = skillbook.to_localtime(skill.endtime);
				var now = moment();
				var skillpercent;
				if(start < now && end > now) {
					// Skill is being trained now
					skillpercent = Math.min(end - now, 86400000) / 864000;
					current_skill = skill;
					$('skill_'+skill.typeid).addClass('training');
				} else if (start > now) {
					// Skill fits in 24 hour window, but isn't being trained now
					skillpercent = Math.min((end-start) - now, 86400000) / 864000;
					$('skill_'+skill.typeid).addClass('training');
				} else {
					return; // Skill training completed
				}
				var title = skill.name + ', Finishes: ' + end.format('LLLL');
				row.adopt(new Element('td', {'style':'width: '+skillpercent+'%;', 'title': title, 'html':'&nbsp;'}))
			});
			var grid = $('pagegrid');
			var template = "<tr><td>Currently Training:</td><td><strong>{name}</strong> {level}</td></tr><tr><td></td><td>{end}</td></tr><tr><td></td><td>{delta}</td></tr>";
			table.adopt(row);
			panel.adopt(table);
			var end = skillbook.to_localtime(current_skill.endtime); 
			var data = {'name': current_skill.name, 'end': end.format('LLLL'), 'delta': end.preciseDiff(moment()), 'level': skillbook.roman(current_skill.level)}
			panel.grab(new Element('table', {'html': new Template().substitute(template, data), 'id': 'current_train'}));
			grid.grab(panel);
		}

		function skill_category(skills, header) {
			var rowtemplate = "<td colspan='2'><b>{name}</b><br />SP: {sp} ({timeconstant}x)</td><td class='right'><img src='/static/img/skill{level}.png' /><br />Level {level}</td>";
			var headertemplate = "<tr style='cursor: pointer'><th style='width: 40%'>{h}</th><th style='width: 40%'><small>{count} skills &mdash; {sp} points</small></th><th>&nbsp;</th></tr>";
			var table = new Element('table', {'class': 'uk-table uk-table-striped uk-table-condensed skills', 'style':'padding-bottom: 10px'});
			var tbody = new Element('tbody');
			var category_sp = 0;

			_.sortBy(skills, function(skill) { return skill.name }).each(function(skill) {
                category_sp += skill.skillpoints
				skill.sp = skillbook.format_number(skill.skillpoints) + '/' + 
					skillbook.format_number(skillbook.sp_next_level(skill.level, skill.timeconstant));
				tbody.grab(new Element('tr', {'html': new Template().substitute(rowtemplate, skill), 'id': 'skill_'+skill.typeid}));
			});

            total_sp += category_sp;

            var data = {'h': skills[0].groupname, 'sp': skillbook.format_number(category_sp), 'count': skills.length};
			var thead = new Element('thead', {'html': new Template().substitute(headertemplate, data)});
			thead.addEvent('click', function(e) {
				tbody.toggle();
			});

			table.adopt(thead, tbody)
			return table;
		}
	}
});

