(function() {
	Object.append(window.skillbook, {
		'api': function(path, cb) {
			new Request.JSON({
				'url': '/api/' + path,
				'onSuccess': cb,
				'onFailure': function(xhr) {
					alert("API GET failure: " + xhr);
				},
				'onComplete': function() {
					var loading = $('loading');
					if (loading)
						loading.setStyle('display', 'none');
					},
			}).get();
		},
		'portrait': function(id, text, img_dir, size, cls) {
			var extension = 'png';
			if (img_dir == 'Character')
				extension = 'jpg';
			var img = new Element('img', {
				'src': 'https://image.eveonline.com/' + img_dir + '/' + id + '_' + size + '.' + extension,
				'alt': text,
				'width': size,
				'height': size,
				'class': cls,
			});
			return img;
		},
		'format_isk': function(number) {
			if(number != null) {
				i = parseInt(number = Math.abs(number).toFixed(2)) + '', 
				j = ((j = i.length) > 3) ? j % 3 : 0; 
				return (j ? i.substr(0, j) + ',' : '') + i.substr(j).replace(/(\d{3})(?=\d)/g, "$1" + ',')
			   		+ ('.' + Math.abs(number - i).toFixed(2).slice(2)) + " ISK";
			} else {
				return "(0 ISK)";
			}
		},
		'format_number': function(number) {
			i = parseInt(number = Math.abs(number)) + '', 
			j = ((j = i.length) > 3) ? j % 3 : 0; 
			return (j ? i.substr(0, j) + ',' : '') + i.substr(j).replace(/(\d{3})(?=\d)/g, "$1" + ',');
		},
		'sp_hour': function(primary, secondary) {
			return (primary + secondary/2) * 60;
		},
		'sp_next_level': function(level, multiplier) {
			var levels = [250, 1415, 8000, 45255, 256000];
			return levels[Math.min(level, 4)] * multiplier;
		},
	});
})();

