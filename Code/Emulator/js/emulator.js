var emulator = { 
  constants: {
    max_iterations: 1
  },
  main_address: 0,
  state: {
    registers: {
      a: 0,
      b: 0,
      c: 0,
      h: 0,
      l: 0,
      ir: 0
    },
    sp: 0,
    pc: 0,
    flags: {
      z: 0,
      c: 0,
      o: 0,
      n: 0
    },
    memory: {
      rom: [ ],
      ram: [ ],
      getData: function(address) { 
        if (address >= 0xFF00) {
          return emulator.handle_input(address);
        }
        return (address >= 0x4000)
          ? emulator.state.memory.ram[address]
          : emulator.state.memory.rom[address];
      },
      setData: function(address, data) {
        if (address >= 0x4000) {
          if (address >= 0xFF00) {
            emulator.handle_output(address, data);
            return;
          }
          emulator.state.memory.ram[address] = data;
        }
      }
    },
    io: {
      textdisplay: null,
    },
    halt: false,
    running: false
  },

  /*
  * Main loop.
  **/
  main: function()
  {
    var i = 0;
    while (i++ < emulator.constants.max_iterations) {
      // We limit the amount of iterations we do with this loop to prevent blocking the event thread.
      // This allows us to maximize the speed the emulator (setTimeout can't go faster than 1 ms.)
      emulator.emulate();
    }

    emulator.update_ui();

    if (emulator.running) {
      setTimeout(emulator.main, 1);
    }
  },

  /*
  * Initialize the emulator.
  ***/
  init: function() 
  { 
    emulator.main_address = (emulator.state.memory.rom[1] << 8) + emulator.state.memory.rom[2];
    emulator.state.io.textdisplay = document.getElementById("textdisplay");

    emulator.disassemble();
  },

  /*
  * Disassemble the program code in memory and display it.
  ***/
  disassemble: function()
  {
    var assembly = (0x10).toHex(4) + ":&nbsp;";
    
    // First display the predefined data.
    for (var i = 0x10; i < emulator.main_address; i++)
    {
      assembly += emulator.state.memory.rom[i].toHex() + "&nbsp;";

      if ((i - 0x10 + 1) % 10 == 0)
      {
        assembly += "<br />&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;";
      }
    }
    
    assembly += "<br />";

    // Now disassemble the machine code.
    for (var i = emulator.main_address; i < emulator.state.memory.rom.length; i++)
    {
      var opcode = emulator.state.memory.rom[i];
      var instruction = emulator.instructions.findByOpcode(opcode);

      assembly += "<a name='code_" + i + "'>" + i.toHex(4) + ":&nbsp;" + opcode.toHex() + "&nbsp;&nbsp;&nbsp;&nbsp;;&nbsp;" + instruction[2] + "</a><br />";

      if (instruction[1] > 1)
      {
        for (var d = i + 1; d < i + instruction[1]; d++)
        {
          var data = emulator.state.memory.rom[d];
          assembly += "<a name='code_" + d + "'>" + d.toHex(4) + ":&nbsp;" + data.toHex() + "</a><br />";
        }

        i += instruction[1] - 1;
      }
    }

    document.getElementById("assembly").innerHTML = assembly;
  },

  /*
  * Highlight the specified address in the disassembled code.
  ***/
  highlight_instruction: function(address)
  {
    var cur = document.getElementsByName("code_" + address)[0];
    var sel = document.getElementsByName("code_" + (address - 15))[0];
    var prev = document.getElementsByClassName("selected_address")[0];

    if (cur) {
      if (prev) {
        prev.className = "";
      }

      cur.className = "selected_address";

      if (sel) {
        sel.scrollIntoView();
      }
    }
  },

  update_ui: function()
  {
    emulator.highlight_instruction(emulator.state.pc);

    document.getElementById("ra").innerText = emulator.state.registers.a.toHex();
    document.getElementById("rb").innerText = emulator.state.registers.b.toHex();
    document.getElementById("rc").innerText = emulator.state.registers.c.toHex();
    document.getElementById("rh").innerText = emulator.state.registers.h.toHex();
    document.getElementById("rl").innerText = emulator.state.registers.l.toHex();
    document.getElementById("rir").innerText = emulator.state.registers.ir.toHex();

    document.getElementById("sp").innerText = emulator.state.sp.toHex(4);
    document.getElementById("pc").innerText = emulator.state.pc.toHex(4);

    document.getElementById("fn").className = "value v" + emulator.state.flags.n;
    document.getElementById("fz").className = "value v" + emulator.state.flags.z;
    document.getElementById("fo").className = "value v" + emulator.state.flags.o;
    document.getElementById("fc").className = "value v" + emulator.state.flags.c;
  },

  handle_output: function(address, data)
  {
    switch (address)
    {
      case 0xFF00:
        emulator.state.io.textdisplay.innerText += String.fromCharCode(data);
    }
  },

  /*
  * Halt the processor.
  ***/
  halt: function() 
  { 
    emulator.state.halt = !emulator.state.halt;
    document.getElementById("button_halt").innerText = emulator.state.halt ? "Continue" : "Halt";
  },

  /*
  * Step by one instruction.
  **/
  step: function()
  {
  },

  /*
  * Stop the emulator.
  **/
  start_stop: function()
  {
    if (emulator.running) {     
      document.getElementById("button_startstop").innerText = "Start";
      emulator.running = false;
    }
    else {
      document.getElementById("button_startstop").innerText = "Stop";
      emulator.running = true;

      emulator.reset();
      emulator.main();
    }
  },

  reset: function()
  {
    emulator.state.pc = emulator.main_address;
    emulator.update_ui();
  },

  /*
  * Emulate the current processor state.
  **/
  emulate: function() 
  { 
    if (emulator.state.halt) {
      return;
    }

    var opcode = emulator.state.memory.getData(emulator.state.pc);
    emulator.state.pc++;

    switch (opcode)
    {
      case 0x00:	// NOP
        break;
      case 0x01:	// MOV A,B
        emulator.state.registers.a = emulator.state.registers.b;
        break;
      case 0x02:	// MOV A,C
        emulator.state.registers.a = emulator.state.registers.c;
        break;
      case 0x03:	// MOV A,H
        emulator.state.registers.a = emulator.state.registers.h;
        break;
      case 0x04:	// MOV A,L
        emulator.state.registers.a = emulator.state.registers.l;
        break;
      case 0x05:	// MOV B,A
        emulator.state.registers.b = emulator.state.registers.a;
        break;
      case 0x06:	// MOV B,C
        emulator.state.registers.b = emulator.state.registers.c;
        break;
      case 0x07:	// MOV B,H
        emulator.state.registers.b = emulator.state.registers.h;
        break;
      case 0x08:	// MOV B,L
        emulator.state.registers.b = emulator.state.registers.l;
        break;
      case 0x09:	// MOV C,A
        emulator.state.registers.c = emulator.state.registers.a;
        break;
      case 0x0A:	// MOV C,B
        emulator.state.registers.c = emulator.state.registers.b;
        break;
      case 0x0B:	// MOV C,H
        emulator.state.registers.c = emulator.state.registers.h;
        break;
      case 0x0C:	// MOV C,L
        emulator.state.registers.c = emulator.state.registers.l;
        break;
      case 0x0D:	// MOV H,A
        emulator.state.registers.h = emulator.state.registers.a;
        break;
      case 0x0E:	// MOV H,B
        emulator.state.registers.h = emulator.state.registers.b;
        break;
      case 0x0F:	// MOV H,C
        emulator.state.registers.h = emulator.state.registers.c;
        break;
      case 0x10:	// MOV H,L
        emulator.state.registers.h = emulator.state.registers.l;
        break;
      case 0x11:	// MOV L,A
        emulator.state.registers.l = emulator.state.registers.a;
        break;
      case 0x12:	// MOV L,B
        emulator.state.registers.l = emulator.state.registers.b;
        break;
      case 0x13:	// MOV L,C
        emulator.state.registers.l = emulator.state.registers.c;
        break;
      case 0x14:	// MOV L,H
        emulator.state.registers.l = emulator.state.registers.h;
        break;
      case 0x15:	// MOV BC,HL
        emulator.state.registers.b = emulator.state.registers.h;
        emulator.state.registers.c = emulator.state.registers.l;
        break;
      case 0x16:	// MOV HL,BC
        emulator.state.registers.h = emulator.state.registers.b;
        emulator.state.registers.l = emulator.state.registers.c;
        break;
      case 0x17:	// MOV A,value
        emulator.state.registers.a = emulator.state.memory.getData(emulator.state.pc++);
        break;
      case 0x18:	// MOV B,value
        emulator.state.registers.b = emulator.state.memory.getData(emulator.state.pc++);
        break;
      case 0x19:	// MOV C,value
        emulator.state.registers.c = emulator.state.memory.getData(emulator.state.pc++);
        break;
      case 0x1A:	// MOV H,value
        emulator.state.registers.h = emulator.state.memory.getData(emulator.state.pc++);
        break;
      case 0x1B:	// MOV L,value
        emulator.state.registers.l = emulator.state.memory.getData(emulator.state.pc++);
        break;
      case 0x1C:	// MOV BC,value
        emulator.state.registers.b = emulator.state.memory.getData(emulator.state.pc++);
        emulator.state.registers.c = emulator.state.memory.getData(emulator.state.pc++);
        break;
      case 0x1D:	// MOV HL,value
        emulator.state.registers.h = emulator.state.memory.getData(emulator.state.pc++);
        emulator.state.registers.l = emulator.state.memory.getData(emulator.state.pc++);
        break;
      case 0x1E:	// MOV A,address
        var addr = (emulator.state.memory.getData(emulator.state.pc++) << 8) + emulator.state.memory.getData(emulator.state.pc++);
        emulator.state.registers.a = emulator.state.memory.getData(addr);
        break;
      case 0x1F:	// MOV B,address
        var addr = (emulator.state.memory.getData(emulator.state.pc++) << 8) + emulator.state.memory.getData(emulator.state.pc++);
        emulator.state.registers.b = emulator.state.memory.getData(addr);
        break;
      case 0x20:	// MOV C,address
        var addr = (emulator.state.memory.getData(emulator.state.pc++) << 8) + emulator.state.memory.getData(emulator.state.pc++);
        emulator.state.registers.c = emulator.state.memory.getData(addr);
        break;
      case 0x21:	// MOV BC,address
        var addr = (emulator.state.memory.getData(emulator.state.pc++) << 8) + emulator.state.memory.getData(emulator.state.pc++);
        emulator.state.registers.b = emulator.state.memory.getData(addr);
        emulator.state.registers.c = emulator.state.memory.getData(addr + 1);
        break;
      case 0x22:	// MOV HL,address
        var addr = (emulator.state.memory.getData(emulator.state.pc++) << 8) + emulator.state.memory.getData(emulator.state.pc++);
        emulator.state.registers.h = emulator.state.memory.getData(addr);
        emulator.state.registers.l = emulator.state.memory.getData(addr + 1);
        break;
      case 0x23:	// MOV address,A
        var addr = (emulator.state.memory.getData(emulator.state.pc++) << 8) + emulator.state.memory.getData(emulator.state.pc++);
        emulator.state.memory.setData(addr, emulator.state.registers.a);
        break;
      case 0x24:	// MOV address,B
        var addr = (emulator.state.memory.getData(emulator.state.pc++) << 8) + emulator.state.memory.getData(emulator.state.pc++);
        emulator.state.memory.setData(addr, emulator.state.registers.b);
        break;
      case 0x25:	// MOV address,C
        var addr = (emulator.state.memory.getData(emulator.state.pc++) << 8) + emulator.state.memory.getData(emulator.state.pc++);
        emulator.state.memory.setData(addr, emulator.state.registers.c);
        break;
      case 0x26:	// MOV address,BC
        var addr = (emulator.state.memory.getData(emulator.state.pc++) << 8) + emulator.state.memory.getData(emulator.state.pc++);
        emulator.state.memory.setData(addr, emulator.state.registers.b);
        emulator.state.memory.setData(addr + 1, emulator.state.registers.c);
        break;
      case 0x27:	// MOV address,HL
        var addr = (emulator.state.memory.getData(emulator.state.pc++) << 8) + emulator.state.memory.getData(emulator.state.pc++);
        emulator.state.memory.setData(addr, emulator.state.registers.h);
        emulator.state.memory.setData(addr + 1, emulator.state.registers.l);
        break;
      case 0x28:	// MOV A,(address)
        var addr = (emulator.state.memory.getData(emulator.state.pc++) << 8) + emulator.state.memory.getData(emulator.state.pc++);
        var data_addr = (emulator.state.memory.getData(addr) << 8) + emulator.state.memory.getData(addr + 1);
        emulator.state.registers.a = emulator.state.memory.getData(data_addr);
        break;
      case 0x29:	// MOV B,(address)
        var addr = (emulator.state.memory.getData(emulator.state.pc++) << 8) + emulator.state.memory.getData(emulator.state.pc++);
        var data_addr = (emulator.state.memory.getData(addr) << 8) + emulator.state.memory.getData(addr + 1);
        emulator.state.registers.b = emulator.state.memory.getData(data_addr);
        break;
      case 0x2A:	// MOV C,(address)
        var addr = (emulator.state.memory.getData(emulator.state.pc++) << 8) + emulator.state.memory.getData(emulator.state.pc++);
        var data_addr = (emulator.state.memory.getData(addr) << 8) + emulator.state.memory.getData(addr + 1);
        emulator.state.registers.c = emulator.state.memory.getData(data_addr);
        break;
      case 0x2B:	// MOV BC,(address)
        var addr = (emulator.state.memory.getData(emulator.state.pc++) << 8) + emulator.state.memory.getData(emulator.state.pc++);
        var data_addr = (emulator.state.memory.getData(addr) << 8) + emulator.state.memory.getData(addr + 1);
        emulator.state.registers.b = emulator.state.memory.getData(data_addr);
        emulator.state.registers.c = emulator.state.memory.getData(data_addr + 1);
        break;
      case 0x2C:	// MOV (address),A
        var addr = (emulator.state.memory.getData(emulator.state.pc++) << 8) + emulator.state.memory.getData(emulator.state.pc++);
        var data_addr = (emulator.state.memory.getData(addr) << 8) + emulator.state.memory.getData(addr + 1);
        emulator.state.memory.setData(data_addr, emulator.state.registers.a);
        break;
      case 0x2D:	// MOV (address),B
        var addr = (emulator.state.memory.getData(emulator.state.pc++) << 8) + emulator.state.memory.getData(emulator.state.pc++);
        var data_addr = (emulator.state.memory.getData(addr) << 8) + emulator.state.memory.getData(addr + 1);
        emulator.state.memory.setData(data_addr, emulator.state.registers.b);
        break;
      case 0x2E:	// MOV (address),C
        var addr = (emulator.state.memory.getData(emulator.state.pc++) << 8) + emulator.state.memory.getData(emulator.state.pc++);
        var data_addr = (emulator.state.memory.getData(addr) << 8) + emulator.state.memory.getData(addr + 1);
        emulator.state.memory.setData(data_addr, emulator.state.registers.c);
        break;
      case 0x2F:	// MOV (address),BC
        var addr = (emulator.state.memory.getData(emulator.state.pc++) << 8) + emulator.state.memory.getData(emulator.state.pc++);
        var data_addr = (emulator.state.memory.getData(addr) << 8) + emulator.state.memory.getData(addr + 1);
        emulator.state.memory.setData(data_addr, emulator.state.registers.b);
        emulator.state.memory.setData(data_addr + 1, emulator.state.registers.c);
        break;
      case 0x30:	// MOV A,(BC)
        var addr = (emulator.state.registers.b << 8) + emulator.state.registers.c;
        emulator.state.registers.a = emulator.state.memory.getData(addr);
        break;
      case 0x31:	// MOV H,(BC)
        var addr = (emulator.state.registers.b << 8) + emulator.state.registers.c;
        emulator.state.registers.h = emulator.state.memory.getData(addr);
        break;
      case 0x32:	// MOV L,(BC)
        var addr = (emulator.state.registers.b << 8) + emulator.state.registers.c;
        emulator.state.registers.l = emulator.state.memory.getData(addr);
        break;
      case 0x33:	// MOV A,(HL)
        var addr = (emulator.state.registers.h << 8) + emulator.state.registers.l;
        emulator.state.registers.a = emulator.state.memory.getData(addr);
        break;
      case 0x34:	// MOV B,(HL)
        var addr = (emulator.state.registers.h << 8) + emulator.state.registers.l;
        emulator.state.registers.b = emulator.state.memory.getData(addr);
        break;
      case 0x35:	// MOV C,(HL)
        var addr = (emulator.state.registers.h << 8) + emulator.state.registers.l;
        emulator.state.registers.c = emulator.state.memory.getData(addr);
        break;
      case 0x36:	// MOV (BC),A
        var addr = (emulator.state.registers.b << 8) + emulator.state.registers.c;
        var data_addr = (emulator.state.memory.getData(addr) << 8) + emulator.state.memory.getData(addr + 1);
        emulator.state.memory.setData(data_addr, emulator.state.registers.a);
        break;
      case 0x37:	// MOV (BC),H
        var addr = (emulator.state.registers.b << 8) + emulator.state.registers.c;
        var data_addr = (emulator.state.memory.getData(addr) << 8) + emulator.state.memory.getData(addr + 1);
        emulator.state.memory.setData(data_addr, emulator.state.registers.h);
        break;
      case 0x38:	// MOV (BC),L
        var addr = (emulator.state.registers.b << 8) + emulator.state.registers.c;
        var data_addr = (emulator.state.memory.getData(addr) << 8) + emulator.state.memory.getData(addr + 1);
        emulator.state.memory.setData(data_addr, emulator.state.registers.l);
        break;
      case 0x39:	// MOV (HL),A
        var addr = (emulator.state.registers.h << 8) + emulator.state.registers.l;
        var data_addr = (emulator.state.memory.getData(addr) << 8) + emulator.state.memory.getData(addr + 1);
        emulator.state.memory.setData(data_addr, emulator.state.registers.a);
        break;
      case 0x3A:	// MOV (HL),B
        var addr = (emulator.state.registers.h << 8) + emulator.state.registers.l;
        var data_addr = (emulator.state.memory.getData(addr) << 8) + emulator.state.memory.getData(addr + 1);
        emulator.state.memory.setData(data_addr, emulator.state.registers.b);
        break;
      case 0x3B:	// MOV (HL),C
        var addr = (emulator.state.registers.h << 8) + emulator.state.registers.l;
        var data_addr = (emulator.state.memory.getData(addr) << 8) + emulator.state.memory.getData(addr + 1);
        emulator.state.memory.setData(data_addr, emulator.state.registers.c);
        break;
      case 0x3C:	// MOV BC,(BC)
        var addr = (emulator.state.registers.b << 8) + emulator.state.registers.c;
        var data_addr = (emulator.state.memory.getData(addr) << 8) + emulator.state.memory.getData(addr + 1);
        emulator.state.registers.b = emulator.state.memory.getData(data_addr);
        emulator.state.registers.c = emulator.state.memory.getData(data_addr + 1);
        break;
      case 0x3D:	// MOV BC,(HL)
        var addr = (emulator.state.registers.h << 8) + emulator.state.registers.l;
        var data_addr = (emulator.state.memory.getData(addr) << 8) + emulator.state.memory.getData(addr + 1);
        emulator.state.registers.b = emulator.state.memory.getData(data_addr);
        emulator.state.registers.c = emulator.state.memory.getData(data_addr + 1);
        break;
      case 0x3E:	// MOV HL,(BC)
        var addr = (emulator.state.registers.b << 8) + emulator.state.registers.c;
        var data_addr = (emulator.state.memory.getData(addr) << 8) + emulator.state.memory.getData(addr + 1);
        emulator.state.registers.h = emulator.state.memory.getData(data_addr);
        emulator.state.registers.l = emulator.state.memory.getData(data_addr + 1);
        break;
      case 0x3F:	// MOV HL,(HL)
        var addr = (emulator.state.registers.h << 8) + emulator.state.registers.l;
        var data_addr = (emulator.state.memory.getData(addr) << 8) + emulator.state.memory.getData(addr + 1);
        emulator.state.registers.h = emulator.state.memory.getData(data_addr);
        emulator.state.registers.l = emulator.state.memory.getData(data_addr + 1);
        break;
      case 0x40:	// MOV (HL),BC
        var addr = (emulator.state.registers.h << 8) + emulator.state.registers.l;
        var data_addr = (emulator.state.memory.getData(addr) << 8) + emulator.state.memory.getData(addr + 1);
        emulator.state.memory.setData(data_addr, emulator.state.registers.b);
        emulator.state.memory.setData(data_addr + 1, emulator.state.registers.c);
        break;
      case 0x41:	// MOV (BC),HL
        var addr = (emulator.state.registers.b << 8) + emulator.state.registers.c;
        var data_addr = (emulator.state.memory.getData(addr) << 8) + emulator.state.memory.getData(addr + 1);
        emulator.state.memory.setData(data_addr, emulator.state.registers.h);
        emulator.state.memory.setData(data_addr + 1, emulator.state.registers.l);
        break;
      case 0x42:	// SP address
        var addr = (emulator.state.memory.getData(emulator.state.pc++) << 8) + emulator.state.memory.getData(emulator.state.pc++);
        emulator.state.sp = addr;
        break;
      case 0x43:	// PUSH A
        emulator.state.memory.setData(emulator.state.sp--, emulator.state.registers.a);
        break;
      case 0x44:	// PUSH B
        emulator.state.memory.setData(emulator.state.sp--, emulator.state.registers.b);
        break;
      case 0x45:	// PUSH C
        emulator.state.memory.setData(emulator.state.sp--, emulator.state.registers.c);
        break;
      case 0x46:	// PUSH H
        emulator.state.memory.setData(emulator.state.sp--, emulator.state.registers.h);
        break;
      case 0x47:	// PUSH L
        emulator.state.memory.setData(emulator.state.sp--, emulator.state.registers.l);
        break;
      case 0x48:	// PUSH BC
        emulator.state.memory.setData(emulator.state.sp--, emulator.state.registers.b);
        emulator.state.memory.setData(emulator.state.sp--, emulator.state.registers.c);
        break;
      case 0x49:	// PUSH HL
        emulator.state.memory.setData(emulator.state.sp--, emulator.state.registers.h);
        emulator.state.memory.setData(emulator.state.sp--, emulator.state.registers.l);
        break;
      case 0x4A:	// PUSH F
        break;
      case 0x4B:	// POP A
        emulator.state.registers.a = emulator.state.memory.getData(emulator.state.sp++);
        break;
      case 0x4C:	// POP B
        emulator.state.registers.b = emulator.state.memory.getData(emulator.state.sp++);
        break;
      case 0x4D:	// POP C
        emulator.state.registers.c = emulator.state.memory.getData(emulator.state.sp++);
        break;
      case 0x4E:	// POP H
        emulator.state.registers.h = emulator.state.memory.getData(emulator.state.sp++);
        break;
      case 0x4F:	// POP L
        emulator.state.registers.l = emulator.state.memory.getData(emulator.state.sp++);
        break;
      case 0x50:	// POP BC
        emulator.state.registers.c = emulator.state.memory.getData(emulator.state.sp++);
        emulator.state.registers.b = emulator.state.memory.getData(emulator.state.sp++);
        break;
      case 0x51:	// POP HL
        emulator.state.registers.l = emulator.state.memory.getData(emulator.state.sp++);
        emulator.state.registers.h = emulator.state.memory.getData(emulator.state.sp++);
        break;
      case 0x52:	// POP F
        break;
      case 0x53:	// ADD A
        emulator.state.registers.a += emulator.state.registers.a;
        emulator.state.flags.c = 0;

        if (emulator.state.registers.a > 255) {
          emulator.state.registers.a = 0;
          emulator.state.flags.c = 1;
        }

        break;
      case 0x54:	// ADD B
        //emulator.state.registers.a += emulator.state.registers.b;
        break;
      case 0x55:	// ADD C
        //emulator.state.registers.a += emulator.state.registers.c;
        break;
      case 0x56:	// ADD H
        //emulator.state.registers.a += emulator.state.registers.h;
        break;
      case 0x57:	// ADD L
        //emulator.state.registers.a += emulator.state.registers.l;
        break;
      case 0x58:	// ADD value
        //emulator.state.registers.a += emulator.state.memory.getData(emulator.state.pc++);
        break;
      case 0x59:	// ADD address
        //var addr = (emulator.state.memory.getData(emulator.state.pc++) << 8) + emulator.state.memory.getData(emulator.state.pc++);
        //emulator.state.registers.a += emulator.state.memory.getData(addr);
        break;
      case 0x5A:	// ADD (address)
        //var addr = (emulator.state.memory.getData(emulator.state.pc++) << 8) + emulator.state.memory.getData(emulator.state.pc++);
        //var data_addr = (emulator.state.memory.getData(addr) << 8) + emulator.state.memory.getData(addr + 1);
        //emulator.state.registers.a += emulator.state.memory.getData(data_addr);
        break;
      case 0x5B:	// ADD (HL)
        //var addr = (emulator.state.registers.b << 8) + emulator.state.registers.c;
        //emulator.state.registers.a += emulator.state.memory.getData(addr);
        break;
      case 0x5C:	// ADC A
        emulator.state.registers.a += emulator.state.registers.a + emulator.state.flags.c;
        emulator.state.flags.c = 0;

        if (emulator.state.registers.a > 255) {
          emulator.state.registers.a = 0;
          emulator.state.flags.c = 1;
        }

        break;
      case 0x5D:	// ADC B
        emulator.state.registers.a += emulator.state.registers.b + emulator.state.flags.c;
        emulator.state.flags.c = 0;

        if (emulator.state.registers.a > 255) {
          emulator.state.registers.a = 0;
          emulator.state.flags.c = 1;
        }

        break;
      case 0x5E:	// ADC C
        break;
      case 0x5F:	// ADC H
        break;
      case 0x60:	// ADC L
        break;
      case 0x61:	// ADC value
        break;
      case 0x62:	// ADC address
        break;
      case 0x63:	// ADC (address)
        break;
      case 0x64:	// ADC (HL)
        break;
      case 0x65:	// SUB A
        break;
      case 0x66:	// SUB B
        break;
      case 0x67:	// SUB C
        break;
      case 0x68:	// SUB H
        break;
      case 0x69:	// SUB L
        break;
      case 0x6A:	// SUB value
        break;
      case 0x6B:	// SUB address
        break;
      case 0x6C:	// SUB (address)
        break;
      case 0x6D:	// SUB (HL)
        break;
      case 0x6E:	// SBC A
        break;
      case 0x6F:	// SBC B
        break;
      case 0x70:	// SBC C
        break;
      case 0x71:	// SBC H
        break;
      case 0x72:	// SBC L
        break;
      case 0x73:	// SBC value
        break;
      case 0x74:	// SBC address
        break;
      case 0x75:	// SBC (address)
        break;
      case 0x76:	// SBC (HL)
        break;
      case 0x77:	// INC A
        break;
      case 0x78:	// INC B
        break;
      case 0x79:	// INC C
        break;
      case 0x7A:	// INC H
        break;
      case 0x7B:	// INC L
        break;
      case 0x7C:	// DEC A
        break;
      case 0x7D:	// DEC B
        break;
      case 0x7E:	// DEC C
        break;
      case 0x7F:	// DEC H
        break;
      case 0x80:	// DEC L
        break;
      case 0x81:	// AND B
        break;
      case 0x82:	// AND C
        break;
      case 0x83:	// AND H
        break;
      case 0x84:	// AND L
        break;
      case 0x85:	// AND value
        break;
      case 0x86:	// AND address
        break;
      case 0x87:	// AND (address)
        break;
      case 0x88:	// AND (HL)
        break;
      case 0x89:	// OR B
        break;
      case 0x8A:	// OR C
        break;
      case 0x8B:	// OR H
        break;
      case 0x8C:	// OR L
        break;
      case 0x8D:	// OR value
        break;
      case 0x8E:	// OR address
        break;
      case 0x8F:	// OR (address)
        break;
      case 0x90:	// OR (HL)
        break;
      case 0x91:	// XOR B
        break;
      case 0x92:	// XOR C
        break;
      case 0x93:	// XOR H
        break;
      case 0x94:	// XOR L
        break;
      case 0x95:	// XOR value
        break;
      case 0x96:	// XOR address
        break;
      case 0x97:	// XOR (address)
        break;
      case 0x98:	// XOR (HL)
        break;
      case 0x99:	// NOT A
        break;
      case 0x9A:	// NOT B
        break;
      case 0x9B:	// NOT C
        break;
      case 0x9C:	// NOT H
        break;
      case 0x9D:	// NOT L
        break;
      case 0x9E:	// NOT value
        break;
      case 0x9F:	// NOT address
        break;
      case 0xA0:	// NOT (address)
        break;
      case 0xA1:	// NOT (HL)
        break;
      case 0xA2:	// SHL B
        break;
      case 0xA3:	// SHL C
        break;
      case 0xA4:	// SHL H
        break;
      case 0xA5:	// SHL L
        break;
      case 0xA6:	// SHL value
        break;
      case 0xA7:	// SHR B
        break;
      case 0xA8:	// SHR C
        break;
      case 0xA9:	// SHR H
        break;
      case 0xAA:	// SHR L
        break;
      case 0xAB:	// SHR value
        break;
      case 0xAC:	// ASR B
        break;
      case 0xAD:	// ASR C
        break;
      case 0xAE:	// ASR H
        break;
      case 0xAF:	// ASR L
        break;
      case 0xB0:	// ASR value
        break;
      case 0xB1:	// ROL B
        break;
      case 0xB2:	// ROL C
        break;
      case 0xB3:	// ROL H
        break;
      case 0xB4:	// ROL L
        break;
      case 0xB5:	// ROL value
        break;
      case 0xB6:	// ROR B
        break;
      case 0xB7:	// ROR C
        break;
      case 0xB8:	// ROR H
        break;
      case 0xB9:	// ROR L
        break;
      case 0xBA:	// ROR value
        break;
      case 0xBB:	// CMP B
        break;
      case 0xBC:	// CMP C
        break;
      case 0xBD:	// CMP H
        break;
      case 0xBE:	// CMP L
        break;
      case 0xBF:	// CMP value
        break;
      case 0xC0:	// CMP address
        break;
      case 0xC1:	// CMP (address)
        break;
      case 0xC2:	// CMP (HL)
        break;
      case 0xC3:	// JMP address
        var addr = (emulator.state.memory.getData(emulator.state.pc++) << 8) + emulator.state.memory.getData(emulator.state.pc++);
        emulator.state.pc = addr;
        break;
      case 0xC4:	// JC address
        break;
      case 0xC5:	// JZ address
        break;
      case 0xC6:	// JN address
        break;
      case 0xC7:	// JO address
        break;
      case 0xC8:	// JNC address
        break;
      case 0xC9:	// JNZ address
        break;
      case 0xCA:	// JP address
        break;
      case 0xCB:	// JNO address
        break;
      case 0xCC:	// CALL address
        emulator.state.memory.setData(emulator.state.sp--, emulator.state.pc >> 8);
        emulator.state.memory.setData(emulator.state.sp--, emulator.state.pc && 8);

        var addr = (emulator.state.memory.getData(emulator.state.pc++) << 8) + emulator.state.memory.getData(emulator.state.pc++);
        emulator.state.pc = addr;
        
        break;
      case 0xCD:	// CC address
        break;
      case 0xCE:	// CZ address
        break;
      case 0xCF:	// CN address
        break;
      case 0xD0:	// CO address
        break;
      case 0xD1:	// CNC address
        break;
      case 0xD2:	// CNZ address
        break;
      case 0xD3:	// CP address
        break;
      case 0xD4:	// CNO address
        break;
      case 0xD5:	// RET
        break;
      case 0xD6:	// RC
        break;
      case 0xD7:	// RZ
        if (emulator.state.flags.z == 1) {
          var lo = emulator.state.memory.getData(emulator.state.sp++);
          var hi = emulator.state.memory.getData(emulator.state.sp++);
          var addr = (hi << 8) + lo;

          emulator.state.pc = addr + 2;
        }
        break;
      case 0xD8:	// RN
        break;
      case 0xD9:	// RO
        break;
      case 0xDA:	// RNC
        break;
      case 0xDB:	// RNZ
        break;
      case 0xDC:	// RP
        break;
      case 0xDD:	// RNO
        break;
      case 0xDE:	// FSET C
        break;
      case 0xDF:	// FSET Z
        break;
      case 0xE0:	// FCLR C
        break;
      case 0xE1:	// FCLR Z
        break;
      case 0xE2:	// HALT
        emulator.state.halt = true;
        break;
      default:
        throw "Unknown opcode: " + opcode.toHex();
    }

    if (emulator.state.pc > 0xFFFF) {
      emulator.start_stop();
    }
  }
}

Number.prototype.toHex = function(len)
{
  var l = len > 0 ? len : 2;
  return "$" + this.toString(16).toUpperCase().padStart(l, '0');
}

document.getElementById("button_halt").addEventListener("click", emulator.halt);
document.getElementById("button_step").addEventListener("click", emulator.step);
document.getElementById("button_startstop").addEventListener("click", emulator.start_stop);

document.write('<script type="text/javascript" src="js/example_program.js"></script>');
document.write('<script type="text/javascript" src="js/instructions.js"></script>');

document.addEventListener("DOMContentLoaded", emulator.init, true);