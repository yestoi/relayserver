makeBoxes = function(count, size_num, key) {
  var boxes = [];
  var max = 6;
  var min = 3;

  for (var i=0; i < count; i++ ) {
    var box = document.createElement('div');
	box.className = 'box size' + size_num; //Math.ceil( Math.random()*(max-min)+min) + Math.ceil( Math.random()*(max-min)+min );
	box.id = key;
    // add box DOM node to array of new elements
    boxes.push( box );
  }

  return boxes;
};

