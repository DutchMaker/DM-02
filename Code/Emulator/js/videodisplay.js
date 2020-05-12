emulator.ui.objects.videodisplay = {
  canvas: { },
  context: { },
  pixeldata: { },
  dataRegister: 0,
  color: 0,
  color_hi: 0,
  color_lo: 0,
  x: 0,
  y: 0,
  width: 0,
  height: 0,
  dirty: false,

  init: function() 
  {
    this.canvas = document.getElementById("videodisplay");
    this.width = this.canvas.width;
    this.height = this.canvas.height;

    this.context = this.canvas.getContext("2d");
    this.context.clearRect(0, 0, this.width, this.height);

    this.pixeldata = this.context.getImageData(0, 0, this.width, this.height);
  },

  reset: function()
  {
    this.x = 0;
    this.y = 0;
    this.dirty = false;

    this.init();
  },

  /*
  * Updates the canvas with pixel data.
  **/
  update: function()
  {
    this.context.putImageData(this.pixeldata, 0, 0);
    this.dirty = false;
  },

  load: function(address, data)
  {
    var command = 0;

    switch (address)
    {
      case 0xFF01:
        this.dataRegister = data;
        break;
      case 0xFF02: 
        command = data;
        break;
    }

    switch (command)
    {
      case 0x01:  // Set color high byte
        this.color_hi = this.dataRegister;
        this.color = 0xFFFFFFFF; // 0xFF000000 | ((this.color_hi << 8) | this.color_lo);
        //this.context.fillStyle = "#" + this.color.toHex().substr(1);
        break;
      case 0x02:  // Set color low byte
        this.color_lo = this.dataRegister;
        this.color = 0xFFFFFFFF; // 0xFF000000 | ((this.color_hi << 8) | this.color_lo);
        //this.context.fillStyle = "#" + this.color.toHex().substr(1);
        break;
      case 0x04:  // Set coordinate X
        this.x = this.dataRegister;
        break;
      case 0x08:  // Set coordinate Y
        this.y = this.dataRegister;
        break;
      case 0x10:  // Write pixel
        //this.context.fillRect(this.x, this.y, 1, 1);
        var index = (this.x + this.y * this.width) * 4;
        this.pixeldata.data[index] = 0xFF;
        this.pixeldata.data[index + 1] = 0xFF;
        this.pixeldata.data[index + 2] = 0xFF;
        this.pixeldata.data[index + 3] = 0xFF;
        this.dirty = true;
        break;
      case 0x20:  // Clear screen
        this.context.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.dirty = true;
        break;
    }
  }
};