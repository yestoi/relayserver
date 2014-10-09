makeBoxes = function(count, size_num, key) {
  var boxes = [];

  for (var i=0; i < count; i++ ) {
    var box = document.createElement('div');
    box.className = 'box size' + size_num;
	box.id = key;
    // add box DOM node to array of new elements
    boxes.push( box );
  }

  return boxes;
};

