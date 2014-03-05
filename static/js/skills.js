window.addEvent('domready', function() {
	skillbook.cache = {}
	skillbook.static = {}
	var clocks = [];
    var total_sp = 0;

	// Fetch the list of skills (static)
	skillbook.api('static/skills', function(skills) {
		skillbook.static = skills
	});

	if(window.location.hash) {
		split = window.location.hash.split('/');
		if(split[0] == '#character') {
			show_character(split[1]);
		} else {
		}
	} else {
		list_characters();
	}


	function list_characters() {
		skillbook.api('characters', function(characters) {
			var grid = $('pagegrid');
			characters.each(function(char) {
				grid.grab(character_row(char));
			});

			function character_row(char) {
				var row = new Element('div', {'class': 'uk-width-1-2', 'style':'padding-bottom: 10px'});
				var article = new Element('article', {'class': 'uk-comment'});
				var header = new Element('header', {'class': 'uk-comment-header'});
				var data = char['corporationname'] + "<br />" + skillbook.format_isk(char['balance']);
				if(char['training_end']) {
					var rowid = "timer_" + char['characterid'];
					data += "<br />Queue finishes in <span id='"+rowid+"'></span>";
					clocks.push( setInterval(function(){update_timer(rowid, char['training_end'])}, 500));
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
			// If no cache, fetch the sheet, skills, and queue
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
		} else {
			display_sheet();
		}

		function display_sheet() {
			var sheet = skillbook.cache[id];
			$('pagetitle').set('text', sheet['name']);

			var row = new Element('div', {'class': 'uk-width-1-1', 'style':'padding-bottom: 10px'});
			var panel = new Element('div', {'class': 'uk-width-1-1'});

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
		function skill_category(skills, header) {
			var rowtemplate = "<td colspan='2'><b>{name}</b><br />SP: {sp} ({timeconstant}x)</td><td class='right'>Level {level}</td>";
			var headertemplate = "<tr style='cursor: pointer'><th style='width: 40%'>{h}</th><th style='width: 40%'><small>{count} skills &mdash; {sp} points</small></th><th>&nbsp;</th></tr>";
			var table = new Element('table', {'class': 'uk-table uk-table-striped uk-table-condensed skills', 'style':'padding-bottom: 10px'});
			var tbody = new Element('tbody');
			var category_sp = 0;

			skills.each(function(skill) {
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

