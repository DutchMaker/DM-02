var emulator = { 
  max_iterations: 1, // Max iterations in main loop before UI update is called.
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
      n: 0,
      clear: function() {
        emulator.state.flags.z = emulator.state.flags.c = emulator.state.flags.o = emulator.state.flags.n = 0;
      }
    },
    memory: {
      rom: [ ],
      ram: [ ],
      get: function(address) { },
      set: function(address, data) { }
    },
    halt: false,
    single_step: false,
    running: false
  },
  ui: {
    objects: {
      a: { },
      b: { },
      c: { },
      h: { },
      l: { },
      ir: { },
      fn: { },
      fz: { },
      fo: { },
      fc: { },
      sp: { },
      pc: { },
      textdisplay: { 
        obj: { },
        data: "",
        dirty: false,
        print: function(str) { }
      }
    },
    prev_highlighted: 0,
    init: function() { },
    update: function() { }
  },

  /*
  * Main loop.
  **/
  main: function()
  {
    if (!emulator.state.single_step) {
      var i = 0;
      while (i++ < emulator.max_iterations) {
        // We limit the amount of iterations we do with this loop to prevent blocking the event thread.
        // This allows us to maximize the speed the emulator (setTimeout can't go faster than 1 ms.)
        emulator.emulate();
      }

      emulator.ui.update();
    }

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
    emulator.state.pc = emulator.main_address;

    document.getElementById("iterations_per_update").value = emulator.max_iterations;
    
    emulator.disassemble();
    emulator.ui.init();
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

  handle_output: function(address, data)
  {
    switch (address)
    {
      case 0xFF00:
        emulator.ui.objects.textdisplay.data += String.fromCharCode(data);
        emulator.ui.objects.textdisplay.dirty = true;
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
    emulator.emulate();
    emulator.ui.update();
  },

  /*
  * Stop the emulator.
  **/
  start_stop: function()
  {
    if (emulator.running) {     
      document.getElementById("button_startstop").innerText = "Restart";
      document.getElementById("button_halt").innerText = "Halt";

      emulator.running = false;
      emulator.state.halt = false;
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
    emulator.ui.prev_highlighted = 0;
    emulator.ui.objects.textdisplay.data = "";
    emulator.ui.objects.textdisplay.dirty = true;

    emulator.state.registers.a = 0;
    emulator.state.registers.b = 0;
    emulator.state.registers.c = 0;
    emulator.state.registers.h = 0;
    emulator.state.registers.l = 0;
    emulator.state.registers.ir = 0;
    emulator.state.sp = 0;
    emulator.state.flags.clear();

    emulator.ui.update();
  },

  /*
  * Emulate the current processor state.
  **/
  emulate: function() 
  { 
    if (emulator.state.halt) {
      return;
    }

    var opcode = emulator.state.memory.get(emulator.state.pc);
    emulator.state.pc++;

    var data, data_hi, data_lo, address, indirect_address;

    // Get data for immediate instructions.
    switch (opcode)
    {
      case 0x17:	// MOV A,value
      case 0x18:	// MOV B,value
      case 0x19:	// MOV C,value
      case 0x1A:	// MOV H,value
      case 0x1B:	// MOV L,value
      case 0x58:	// ADD value
      case 0x61:	// ADC value
      case 0x6A:	// SUB value
      case 0x73:	// SBC value
      case 0x85:	// AND value
      case 0x8D:	// OR value
      case 0x95:	// XOR value
      case 0x9E:	// NOT value
      case 0xA6:	// SHL value
      case 0xAB:	// SHR value
      case 0xB0:	// ASR value
      case 0xB5:	// ROL value
      case 0xBA:	// ROR value
      case 0xBF:	// CMP value
        data = emulator.state.memory.get(emulator.state.pc++);
        break;
      case 0x1C:	// MOV BC,value
      case 0x1D:	// MOV HL,value
        data_hi = emulator.state.memory.get(emulator.state.pc++);
        data_lo = emulator.state.memory.get(emulator.state.pc++);
        break;
    }

    // Get data for register instructions.
    switch (opcode)
    {
      case 0x05:	// MOV B,A
      case 0x09:	// MOV C,A
      case 0x0D:	// MOV H,A
      case 0x11:	// MOV L,A
      case 0x23:	// MOV address,A
      case 0x2C:	// MOV (address),A
      case 0x36:	// MOV (BC),A
      case 0x39:	// MOV (HL),A
      case 0x43:	// PUSH A
      case 0x53:	// ADD A
      case 0x5C:	// ADC A
      case 0x65:	// SUB A
      case 0x99:	// NOT A
        data = emulator.state.registers.a;
        break;
      case 0x01:	// MOV A,B
      case 0x0A:	// MOV C,B
      case 0x0E:	// MOV H,B
      case 0x12:	// MOV L,B
      case 0x24:	// MOV address,B
      case 0x2D:	// MOV (address),B
      case 0x3A:	// MOV (HL),B
      case 0x44:	// PUSH B
      case 0x54:	// ADD B
      case 0x5D:	// ADC B
      case 0x66:	// SUB B
      case 0x81:	// AND B
      case 0x89:	// OR B
      case 0x91:	// XOR B
      case 0x9A:	// NOT B
      case 0xA2:	// SHL B
      case 0xA7:	// SHR B
      case 0xAC:	// ASR B
      case 0xB1:	// ROL B
      case 0xB6:	// ROR B
      case 0xBB:	// CMP B
        data = emulator.state.registers.b;
        break;
      case 0x02:	// MOV A,C
      case 0x06:	// MOV B,C
      case 0x0F:	// MOV H,C
      case 0x13:	// MOV L,C
      case 0x25:	// MOV address,C
      case 0x2E:	// MOV (address),C
      case 0x3B:	// MOV (HL),C
      case 0x45:	// PUSH C
      case 0x55:	// ADD C
      case 0x5E:	// ADC C
      case 0x67:	// SUB C
      case 0x82:	// AND C
      case 0x8A:	// OR C
      case 0x92:	// XOR C
      case 0x9B:	// NOT C
      case 0xA3:	// SHL C
      case 0xA8:	// SHR C
      case 0xAD:	// ASR C
      case 0xB2:	// ROL C
      case 0xB7:	// ROR C
      case 0xBC:	// CMP C
        data = emulator.state.registers.c;
        break;
      case 0x03:	// MOV A,H
      case 0x07:	// MOV B,H
      case 0x0B:	// MOV C,H
      case 0x14:	// MOV L,H
      case 0x37:	// MOV (BC),H
      case 0x46:	// PUSH H
      case 0x56:	// ADD H
      case 0x5F:	// ADC H
      case 0x68:	// SUB H
      case 0x83:	// AND H
      case 0x8B:	// OR H
      case 0x93:	// XOR H
      case 0x9C:	// NOT H
      case 0xA4:	// SHL H
      case 0xA9:	// SHR H
      case 0xAE:	// ASR H
      case 0xB3:	// ROL H
      case 0xB8:	// ROR H
      case 0xBD:	// CMP H
        data = emulator.state.registers.h;
        break;
      case 0x04:	// MOV A,L
      case 0x08:	// MOV B,L
      case 0x0C:	// MOV C,L
      case 0x10:	// MOV H,L
      case 0x38:	// MOV (BC),L
      case 0x47:	// PUSH L
      case 0x57:	// ADD L
      case 0x60:	// ADC L
      case 0x69:	// SUB L
      case 0x84:	// AND L
      case 0x8C:	// OR L
      case 0x94:	// XOR L
      case 0x9D:	// NOT L
      case 0xA5:	// SHL L
      case 0xAA:	// SHR L
      case 0xAF:	// ASR L
      case 0xB4:	// ROL L
      case 0xB9:	// ROR L
      case 0xBE:	// CMP L
        data = emulator.state.registers.l;
        break;
      case 0x15:	// MOV BC,HL
      case 0x27:	// MOV address,HL
      case 0x49:	// PUSH HL
        data_hi = emulator.state.registers.h;
        data_lo = emulator.state.registers.l;
        break;
      case 0x16:	// MOV HL,BC
      case 0x26:	// MOV address,BC 
      case 0x2F:	// MOV (address),BC
      case 0x48:	// PUSH BC
        data_hi = emulator.state.registers.b;
        data_lo = emulator.state.registers.c;
        break;
    }

    // Get data and address for direct addressing instructions.
    switch (opcode)
    {
      case 0x23:	// MOV address,A
      case 0x24:	// MOV address,B
      case 0x25:	// MOV address,C
        address = (emulator.state.memory.get(emulator.state.pc++) << 8) + emulator.state.memory.get(emulator.state.pc++);
        break;
      case 0x1E:	// MOV A,address
      case 0x1F:	// MOV B,address
      case 0x20:	// MOV C,address
      case 0x42:	// SP address
      case 0x59:	// ADD address
      case 0x62:	// ADC address
      case 0x6B:	// SUB address
      case 0x74:	// SBC address
      case 0x86:	// AND address
      case 0x8E:	// OR address
      case 0x96:	// XOR address
      case 0x9F:	// NOT address
      case 0xC0:	// CMP address
      case 0xC3:	// JMP address
      case 0xC4:	// JC address
      case 0xC5:	// JZ address
      case 0xC6:	// JN address
      case 0xC7:	// JO address
      case 0xC8:	// JNC address
      case 0xC9:	// JNZ address
      case 0xCA:	// JP address
      case 0xCB:	// JNO address
      case 0xCC:	// CALL address
      case 0xCD:	// CC address
      case 0xCE:	// CZ address
      case 0xCF:	// CN address
      case 0xD0:	// CO address
      case 0xD1:	// CNC address
      case 0xD2:	// CNZ address
      case 0xD3:	// CP address
      case 0xD4:	// CNO address
        address = (emulator.state.memory.get(emulator.state.pc++) << 8) + emulator.state.memory.get(emulator.state.pc++);
        data = emulator.state.memory.get(address);
        break;
      case 0x26:	// MOV address,BC 
      case 0x27:	// MOV address,HL
        address = (emulator.state.memory.get(emulator.state.pc++) << 8) + emulator.state.memory.get(emulator.state.pc++);
        break;
      case 0x21:	// MOV BC,address
      case 0x22:	// MOV HL,address
        address = (emulator.state.memory.get(emulator.state.pc++) << 8) + emulator.state.memory.get(emulator.state.pc++);
        data_hi = emulator.state.memory.get(address);
        data_lo = emulator.state.memory.get(address + 1);
        break;
    }

    // Get data for indirect addressing instructions.
    switch (opcode)
    {
      case 0x2C:	// MOV (address),A
      case 0x2D:	// MOV (address),B
      case 0x2E:	// MOV (address),C
      case 0x2F:	// MOV (address),BC
        address = (emulator.state.memory.get(emulator.state.pc++) << 8) + emulator.state.memory.get(emulator.state.pc++);
        indirect_address = (emulator.state.memory.get(address) << 8) + emulator.state.memory.get(address + 1);
        break;
      case 0x28:	// MOV A,(address)
      case 0x29:	// MOV B,(address)
      case 0x2A:	// MOV C,(address)
      case 0x2B:	// MOV BC,(address)
      case 0x5A:	// ADD (address)
      case 0x63:	// ADC (address)
      case 0x6C:	// SUB (address)
      case 0x75:	// SBC (address)
      case 0x87:	// AND (address)
      case 0x8F:	// OR (address)
      case 0x97:	// XOR (address)
      case 0xA0:	// NOT (address)
      case 0xC1:	// CMP (address)
        address = (emulator.state.memory.get(emulator.state.pc++) << 8) + emulator.state.memory.get(emulator.state.pc++);
        indirect_address = (emulator.state.memory.get(address) << 8) + emulator.state.memory.get(address + 1);
        data = emulator.state.memory.get(indirect_address);
        break;
    }

    // Get data for indirect register BC addressing.
    switch (opcode)
    {
      case 0x36:	// MOV (BC),A
      case 0x37:	// MOV (BC),H
      case 0x38:	// MOV (BC),L
        address = indirect_address = (emulator.state.registers.b << 8) + emulator.state.registers.c;
        break;
      case 0x30:	// MOV A,(BC)
      case 0x31:	// MOV H,(BC)
      case 0x32:	// MOV L,(BC)
        address = indirect_address = (emulator.state.registers.b << 8) + emulator.state.registers.c;
        data = emulator.state.memory.get(address);
        break;
      case 0x41:	// MOV (BC),HL
        address = indirect_address = (emulator.state.registers.b << 8) + emulator.state.registers.c;
        break;
      case 0x3C:	// MOV BC,(BC)
      case 0x3E:	// MOV HL,(BC)
        address = indirect_address = (emulator.state.registers.b << 8) + emulator.state.registers.c;
        data_hi = emulator.state.memory.get(address);
        data_lo = emulator.state.memory.get(address + 1);
        break;
    }

    // Get data for indirect register HL addressing.
    switch (opcode)
    {
      case 0x40:	// MOV (HL),BC
      case 0x39:	// MOV (HL),A
      case 0x3A:	// MOV (HL),B
      case 0x3B:	// MOV (HL),C
        address = indirect_address = (emulator.state.registers.h << 8) + emulator.state.registers.l;
        break;
      case 0x3D:	// MOV BC,(HL)
      case 0x3F:	// MOV HL,(HL)
        address = indirect_address = (emulator.state.registers.h << 8) + emulator.state.registers.l;
        data_hi = emulator.state.memory.get(address);
        data_lo = emulator.state.memory.get(address + 1);
        break;
      case 0x33:	// MOV A,(HL)
      case 0x34:	// MOV B,(HL)
      case 0x35:	// MOV C,(HL)
      case 0x5B:	// ADD (HL)
      case 0x64:	// ADC (HL)
      case 0x6D:	// SUB (HL)
      case 0x76:	// SBC (HL)
      case 0x88:	// AND (HL)
      case 0x90:	// OR (HL)
      case 0x98:	// XOR (HL)
      case 0xA1:	// NOT (HL)
      case 0xC2:	// CMP (HL)
        address = indirect_address = (emulator.state.registers.h << 8) + emulator.state.registers.l;
        data = emulator.state.memory.get(address);
        break;
    }

    var flag_update = false;

    switch (opcode)
    {
      case 0x53:	// ADD A
      case 0x54:	// ADD B
      case 0x55:	// ADD C
      case 0x56:	// ADD H
      case 0x57:	// ADD L
      case 0x58:	// ADD value
      case 0x59:	// ADD address
      case 0x5A:	// ADD (address)
      case 0x5B:	// ADD (HL)
      case 0x5C:	// ADC A
      case 0x5D:	// ADC B
      case 0x5E:	// ADC C
      case 0x5F:	// ADC H
      case 0x60:	// ADC L
      case 0x61:	// ADC value
      case 0x62:	// ADC address
      case 0x63:	// ADC (address)
      case 0x64:	// ADC (HL)
      case 0x65:	// SUB A
      case 0x66:	// SUB B
      case 0x67:	// SUB C
      case 0x68:	// SUB H
      case 0x69:	// SUB L
      case 0x6A:	// SUB value
      case 0x6B:	// SUB address
      case 0x6C:	// SUB (address)
      case 0x6D:	// SUB (HL)
      case 0x6E:	// SBC A
      case 0x6F:	// SBC B
      case 0x70:	// SBC C
      case 0x71:	// SBC H
      case 0x72:	// SBC L
      case 0x73:	// SBC value
      case 0x74:	// SBC address
      case 0x75:	// SBC (address)
      case 0x76:	// SBC (HL)
      case 0x77:	// INC A
      case 0x7C:	// DEC A
      case 0x81:	// AND B
      case 0x82:	// AND C
      case 0x83:	// AND H
      case 0x84:	// AND L
      case 0x85:	// AND value
      case 0x86:	// AND address
      case 0x87:	// AND (address)
      case 0x88:	// AND (HL)
      case 0x89:	// OR B
      case 0x8A:	// OR C
      case 0x8B:	// OR H
      case 0x8C:	// OR L
      case 0x8D:	// OR value
      case 0x8E:	// OR address
      case 0x8F:	// OR (address)
      case 0x90:	// OR (HL)
      case 0x91:	// XOR B
      case 0x92:	// XOR C
      case 0x93:	// XOR H
      case 0x94:	// XOR L
      case 0x95:	// XOR value
      case 0x96:	// XOR address
      case 0x97:	// XOR (address)
      case 0x98:	// XOR (HL)
      case 0x99:	// NOT A
      case 0x9A:	// NOT B
      case 0x9B:	// NOT C
      case 0x9C:	// NOT H
      case 0x9D:	// NOT L
      case 0x9E:	// NOT value
      case 0x9F:	// NOT address
      case 0xA0:	// NOT (address)
      case 0xA1:	// NOT (HL)
      case 0xA2:	// SHL B
      case 0xA3:	// SHL C
      case 0xA4:	// SHL H
      case 0xA5:	// SHL L
      case 0xA6:	// SHL value
      case 0xA7:	// SHR B
      case 0xA8:	// SHR C
      case 0xA9:	// SHR H
      case 0xAA:	// SHR L
      case 0xAB:	// SHR value
      case 0xAC:	// ASR B
      case 0xAD:	// ASR C
      case 0xAE:	// ASR H
      case 0xAF:	// ASR L
      case 0xB0:	// ASR value
      case 0xB1:	// ROL B
      case 0xB2:	// ROL C
      case 0xB3:	// ROL H
      case 0xB4:	// ROL L
      case 0xB5:	// ROL value
      case 0xB6:	// ROR B
      case 0xB7:	// ROR C
      case 0xB8:	// ROR H
      case 0xB9:	// ROR L
      case 0xBA:	// ROR value
        flag_update = true;
        break;
    }

    // Update the emulator state.
    switch (opcode)
    {
      case 0x00:	// NOP
        break;
      case 0x01:	// MOV A,B
      case 0x02:	// MOV A,C
      case 0x03:	// MOV A,H
      case 0x04:	// MOV A,L
      case 0x17:	// MOV A,value
      case 0x1E:	// MOV A,address
      case 0x28:	// MOV A,(address)
      case 0x30:	// MOV A,(BC)
      case 0x33:	// MOV A,(HL)
        emulator.state.registers.a = data;
        break;
      case 0x05:	// MOV B,A
      case 0x06:	// MOV B,C
      case 0x07:	// MOV B,H
      case 0x08:	// MOV B,L
      case 0x18:	// MOV B,value
      case 0x1F:	// MOV B,address
      case 0x29:	// MOV B,(address)
      case 0x34:	// MOV B,(HL)
        emulator.state.registers.b = data;
        break;
      case 0x09:	// MOV C,A
      case 0x0A:	// MOV C,B
      case 0x0B:	// MOV C,H
      case 0x0C:	// MOV C,L
      case 0x19:	// MOV C,value
      case 0x20:	// MOV C,address
      case 0x2A:	// MOV C,(address)
      case 0x35:	// MOV C,(HL)
        emulator.state.registers.c = data;
        break;
      case 0x0D:	// MOV H,A
      case 0x0E:	// MOV H,B
      case 0x0F:	// MOV H,C
      case 0x10:	// MOV H,L
      case 0x1A:	// MOV H,value
      case 0x31:	// MOV H,(BC)
        emulator.state.registers.h = data;
        break;
      case 0x11:	// MOV L,A
      case 0x12:	// MOV L,B
      case 0x13:	// MOV L,C
      case 0x14:	// MOV L,H
      case 0x1B:	// MOV L,value
      case 0x32:	// MOV L,(BC)
        emulator.state.registers.l = data;
        break;
      case 0x15:	// MOV BC,HL
      case 0x1C:	// MOV BC,value
      case 0x21:	// MOV BC,address
      case 0x2B:	// MOV BC,(address)
      case 0x3C:	// MOV BC,(BC)
      case 0x3D:	// MOV BC,(HL)
        emulator.state.registers.b = data_hi;
        emulator.state.registers.c = data_lo;
        break;
      case 0x16:	// MOV HL,BC
      case 0x1D:	// MOV HL,value
      case 0x22:	// MOV HL,address
      case 0x3E:	// MOV HL,(BC)
      case 0x3F:	// MOV HL,(HL)
        emulator.state.registers.h = data_hi;
        emulator.state.registers.l = data_lo;
        break;
      case 0x23:	// MOV address,A
      case 0x24:	// MOV address,B
      case 0x25:	// MOV address,C
        emulator.state.memory.set(address, data);
        break;
      case 0x2C:	// MOV (address),A
      case 0x2D:	// MOV (address),B
      case 0x2E:	// MOV (address),C
      case 0x36:	// MOV (BC),A
      case 0x37:	// MOV (BC),H
      case 0x38:	// MOV (BC),L
      case 0x39:	// MOV (HL),A
      case 0x3A:	// MOV (HL),B
      case 0x3B:	// MOV (HL),C
        emulator.state.memory.set(indirect_address, data);
        break;
      case 0x26:	// MOV address,BC
      case 0x27:	// MOV address,HL
      case 0x2F:	// MOV (address),BC
        emulator.state.memory.set(address, data_hi);
        emulator.state.memory.set(address + 1, data_lo);
        break;
      case 0x40:	// MOV (HL),BC
      case 0x41:	// MOV (BC),HL
        emulator.state.memory.set(indirect_address, data_hi);
        emulator.state.memory.set(indirect_address + 1, data_lo);
        break;
      case 0x42:	// SP address
        emulator.state.sp = address;
        break;
      case 0x43:	// PUSH A
      case 0x44:	// PUSH B
      case 0x45:	// PUSH C
      case 0x46:	// PUSH H
      case 0x47:	// PUSH L
        emulator.state.memory.set(emulator.state.sp--, data);
        break;
      case 0x48:	// PUSH BC
      case 0x49:	// PUSH HL
        emulator.state.memory.set(emulator.state.sp--, data_hi);
        emulator.state.memory.set(emulator.state.sp--, data_lo);
        break;
      case 0x4A:	// PUSH F
        console.log("Warning: Instruction " + opcode.toHex() + " not implemented");
        break;
      case 0x4B:	// POP A
        emulator.state.registers.a = emulator.state.memory.get(emulator.state.sp++);
        break;
      case 0x4C:	// POP B
        emulator.state.registers.b = emulator.state.memory.get(emulator.state.sp++);
        break;
      case 0x4D:	// POP C
        emulator.state.registers.c = emulator.state.memory.get(emulator.state.sp++);
        break;
      case 0x4E:	// POP H
        emulator.state.registers.h = emulator.state.memory.get(emulator.state.sp++);
        break;
      case 0x4F:	// POP L
        emulator.state.registers.l = emulator.state.memory.get(emulator.state.sp++);
        break;
      case 0x50:	// POP BC
        emulator.state.registers.c = emulator.state.memory.get(emulator.state.sp++);
        emulator.state.registers.b = emulator.state.memory.get(emulator.state.sp++);
        break;
      case 0x51:	// POP HL
        emulator.state.registers.l = emulator.state.memory.get(emulator.state.sp++);
        emulator.state.registers.h = emulator.state.memory.get(emulator.state.sp++);
        break;
      case 0x52:	// POP F
        console.log("Warning: Instruction " + opcode.toHex() + " not implemented");
        break;
      case 0x53:	// ADD A
      case 0x54:	// ADD B
      case 0x55:	// ADD C
      case 0x56:	// ADD H
      case 0x57:	// ADD L
      case 0x58:	// ADD value
      case 0x59:	// ADD address
      case 0x5A:	// ADD (address)
      case 0x5B:	// ADD (HL)
        emulator.state.registers.a += data;
        break;
      case 0x5C:	// ADC A
      case 0x5D:	// ADC B
      case 0x5E:	// ADC C
      case 0x5F:	// ADC H
      case 0x60:	// ADC L
      case 0x61:	// ADC value
      case 0x62:	// ADC address
      case 0x63:	// ADC (address)
      case 0x64:	// ADC (HL)
        emulator.state.registers.a += data + emulator.state.flags.c;
        break;
      case 0x65:	// SUB A
      case 0x66:	// SUB B
      case 0x67:	// SUB C
      case 0x68:	// SUB H
      case 0x69:	// SUB L
      case 0x6A:	// SUB value
      case 0x6B:	// SUB address
      case 0x6C:	// SUB (address)
      case 0x6D:	// SUB (HL)
        emulator.state.registers.a -= data;
        break;
      case 0x6E:	// SBC A
      case 0x6F:	// SBC B
      case 0x70:	// SBC C
      case 0x71:	// SBC H
      case 0x72:	// SBC L
      case 0x73:	// SBC value
      case 0x74:	// SBC address
      case 0x75:	// SBC (address)
      case 0x76:	// SBC (HL)
        emulator.state.registers.a -= (data + emulator.state.flags.c);
        break;
      case 0x77:	// INC A
        emulator.state.registers.a++;
        break;
      case 0x78:	// INC B
        emulator.state.flags.clear();
        if (++emulator.state.registers.b > 255) {
          emulator.state.flags.o = 1;
          emulator.state.flags.c = 1;
          emulator.state.flags.z = 1;
          emulator.state.registers.b = 0;
        }
        break;
      case 0x79:	// INC C
        emulator.state.flags.clear();
        if (++emulator.state.registers.c > 255) {
          emulator.state.flags.o = 1;
          emulator.state.flags.c = 1;
          emulator.state.flags.z = 1;
          emulator.state.registers.c = 0;
        }
        break;
      case 0x7A:	// INC H
        emulator.state.flags.clear();
        if (++emulator.state.registers.h > 255) {
          emulator.state.flags.o = 1;
          emulator.state.flags.c = 1;
          emulator.state.flags.z = 1;
          emulator.state.registers.h = 0;
        }
        break;
      case 0x7B:	// INC L
        emulator.state.flags.clear();
        if (++emulator.state.registers.l > 255) {
          emulator.state.flags.o = 1;
          emulator.state.flags.c = 1;
          emulator.state.flags.z = 1;
          emulator.state.registers.l = 0;
        }
        break;
      case 0x7C:	// DEC A
        emulator.state.registers.a--;
        break;
      case 0x7D:	// DEC B
        emulator.state.flags.clear();
        if (--emulator.state.registers.b < 0) {
          emulator.state.flags.o = 1;
          emulator.state.flags.c = 1;
          emulator.state.flags.n = 1;
          emulator.state.registers.b = 255;
        }
        break;
      case 0x7E:	// DEC C
        emulator.state.flags.clear();
        if (--emulator.state.registers.c < 0) {
          emulator.state.flags.o = 1;
          emulator.state.flags.c = 1;
          emulator.state.flags.n = 1;
          emulator.state.registers.c = 255;
        }
        break;
      case 0x7F:	// DEC H
        emulator.state.flags.clear();
        if (--emulator.state.registers.h < 0) {
          emulator.state.flags.o = 1;
          emulator.state.flags.c = 1;
          emulator.state.flags.n = 1;
          emulator.state.registers.h = 255;
        }
        break;
      case 0x80:	// DEC L
        emulator.state.flags.clear();
        if (--emulator.state.registers.l < 0) {
          emulator.state.flags.o = 1;
          emulator.state.flags.c = 1;
          emulator.state.flags.n = 1;
          emulator.state.registers.l = 255;
        }
        break;
      case 0x81:	// AND B
      case 0x82:	// AND C
      case 0x83:	// AND H
      case 0x84:	// AND L
      case 0x85:	// AND value
      case 0x86:	// AND address
      case 0x87:	// AND (address)
      case 0x88:	// AND (HL)
        console.log("Warning: Instruction " + opcode.toHex() + " not implemented");
        break;
      case 0x89:	// OR B
      case 0x8A:	// OR C
      case 0x8B:	// OR H
      case 0x8C:	// OR L
      case 0x8D:	// OR value
      case 0x8E:	// OR address
      case 0x8F:	// OR (address)
      case 0x90:	// OR (HL)
        console.log("Warning: Instruction " + opcode.toHex() + " not implemented");
        break;
      case 0x91:	// XOR B
      case 0x92:	// XOR C
      case 0x93:	// XOR H
      case 0x94:	// XOR L
      case 0x95:	// XOR value
      case 0x96:	// XOR address
      case 0x97:	// XOR (address)
      case 0x98:	// XOR (HL)
        console.log("Warning: Instruction " + opcode.toHex() + " not implemented");
        break;
      case 0x99:	// NOT A
      case 0x9A:	// NOT B
      case 0x9B:	// NOT C
      case 0x9C:	// NOT H
      case 0x9D:	// NOT L
      case 0x9E:	// NOT value
      case 0x9F:	// NOT address
      case 0xA0:	// NOT (address)
      case 0xA1:	// NOT (HL)
        console.log("Warning: Instruction " + opcode.toHex() + " not implemented");
        break;
      case 0xA2:	// SHL B
      case 0xA3:	// SHL C
      case 0xA4:	// SHL H
      case 0xA5:	// SHL L
      case 0xA6:	// SHL value
        console.log("Warning: Instruction " + opcode.toHex() + " not implemented");
        break;
      case 0xA7:	// SHR B
      case 0xA8:	// SHR C
      case 0xA9:	// SHR H
      case 0xAA:	// SHR L
      case 0xAB:	// SHR value
        console.log("Warning: Instruction " + opcode.toHex() + " not implemented");
        break;
      case 0xAC:	// ASR B
      case 0xAD:	// ASR C
      case 0xAE:	// ASR H
      case 0xAF:	// ASR L
      case 0xB0:	// ASR value
        console.log("Warning: Instruction " + opcode.toHex() + " not implemented");      
        break;
      case 0xB1:	// ROL B
      case 0xB2:	// ROL C
      case 0xB3:	// ROL H
      case 0xB4:	// ROL L
      case 0xB5:	// ROL value
        console.log("Warning: Instruction " + opcode.toHex() + " not implemented");
        break;
      case 0xB6:	// ROR B
      case 0xB7:	// ROR C
      case 0xB8:	// ROR H
      case 0xB9:	// ROR L
      case 0xBA:	// ROR value
        console.log("Warning: Instruction " + opcode.toHex() + " not implemented");
        break;
      case 0xBB:	// CMP B
      case 0xBC:	// CMP C
      case 0xBD:	// CMP H
      case 0xBE:	// CMP L
      case 0xBF:	// CMP value
      case 0xC0:	// CMP address
      case 0xC1:	// CMP (address)
      case 0xC2:	// CMP (HL)
        emulator.state.flags.clear();
        if (emulator.state.registers.a - data < 0) {
          emulator.state.flags.o = 1;
          emulator.state.flags.c = 1;
          emulator.state.flags.z = 0;
          emulator.state.flags.n = 1;
          emulator.state.registers.a = 255;
        }
        else if (emulator.state.registers.a - data == 0) {
          emulator.state.flags.z = 1;
        }
        break;
      case 0xC3:	// JMP address
        emulator.state.pc = address;
        break;
      case 0xC4:	// JC address
        console.log("Warning: Instruction " + opcode.toHex() + " not implemented");
        break;
      case 0xC5:	// JZ address
        console.log("Warning: Instruction " + opcode.toHex() + " not implemented");
        break;
      case 0xC6:	// JN address
        console.log("Warning: Instruction " + opcode.toHex() + " not implemented");
        break;
      case 0xC7:	// JO address
        console.log("Warning: Instruction " + opcode.toHex() + " not implemented");
        break;
      case 0xC8:	// JNC address
        console.log("Warning: Instruction " + opcode.toHex() + " not implemented");
        break;
      case 0xC9:	// JNZ address
        console.log("Warning: Instruction " + opcode.toHex() + " not implemented");
        break;
      case 0xCA:	// JP address
        console.log("Warning: Instruction " + opcode.toHex() + " not implemented");
        break;
      case 0xCB:	// JNO address
        console.log("Warning: Instruction " + opcode.toHex() + " not implemented");
        break;
      case 0xCC:	// CALL address
        emulator.state.memory.set(emulator.state.sp--, emulator.state.pc >> 8);
        emulator.state.memory.set(emulator.state.sp--, emulator.state.pc & 0xFF);
        emulator.state.pc = address;
        break;
      case 0xCD:	// CC address
        console.log("Warning: Instruction " + opcode.toHex() + " not implemented");
        break;
      case 0xCE:	// CZ address
        console.log("Warning: Instruction " + opcode.toHex() + " not implemented");
        break;
      case 0xCF:	// CN address
        console.log("Warning: Instruction " + opcode.toHex() + " not implemented");
        break;
      case 0xD0:	// CO address
        console.log("Warning: Instruction " + opcode.toHex() + " not implemented");
        break;
      case 0xD1:	// CNC address
        console.log("Warning: Instruction " + opcode.toHex() + " not implemented");
        break;
      case 0xD2:	// CNZ address
        console.log("Warning: Instruction " + opcode.toHex() + " not implemented");
        break;
      case 0xD3:	// CP address
        console.log("Warning: Instruction " + opcode.toHex() + " not implemented");
        break;
      case 0xD4:	// CNO address
        console.log("Warning: Instruction " + opcode.toHex() + " not implemented");
        break;
      case 0xD5:	// RET
        var lo = emulator.state.memory.get(++emulator.state.sp);
        var hi = emulator.state.memory.get(++emulator.state.sp);
        var addr = (hi << 8) + lo;

        emulator.state.pc = addr;
        break;
      case 0xD6:	// RC
        console.log("Warning: Instruction " + opcode.toHex() + " not implemented");
        break;
      case 0xD7:	// RZ
        if (emulator.state.flags.z == 1) {
          var lo = emulator.state.memory.get(++emulator.state.sp);
          var hi = emulator.state.memory.get(++emulator.state.sp);
          var addr = (hi << 8) + lo;

          emulator.state.pc = addr;
        }
        break;
      case 0xD8:	// RN
        console.log("Warning: Instruction " + opcode.toHex() + " not implemented");
        break;
      case 0xD9:	// RO
        console.log("Warning: Instruction " + opcode.toHex() + " not implemented");
        break;
      case 0xDA:	// RNC
        console.log("Warning: Instruction " + opcode.toHex() + " not implemented");
        break;
      case 0xDB:	// RNZ
        console.log("Warning: Instruction " + opcode.toHex() + " not implemented");
        break;
      case 0xDC:	// RP
        console.log("Warning: Instruction " + opcode.toHex() + " not implemented");
        break;
      case 0xDD:	// RNO
        console.log("Warning: Instruction " + opcode.toHex() + " not implemented"); 
        break;
      case 0xDE:	// FSET C
        emulator.state.flags.c = 1;
        break;
      case 0xDF:	// FSET Z
        emulator.state.flags.z = 1;
        break;
      case 0xE0:	// FCLR C
        emulator.state.flags.c = 0;
        break;
      case 0xE1:	// FCLR Z
        emulator.state.flags.z = 0;
        break;
      case 0xE2:	// HALT
        emulator.state.halt = true;
        break;
      default:
        throw "Unknown opcode: " + opcode.toHex();
    }

    if (flag_update) {
      emulator.state.flags.clear();

      if (emulator.state.registers.a == 0)
      {
        emulator.state.flags.z = 1;
      }

      if (emulator.state.registers.a > 255) {
        emulator.state.flags.o = 1;
        emulator.state.flags.c = 1;
        emulator.state.flags.z = 1;
        emulator.state.registers.a = 0;
      }

      if (emulator.state.registers.a < 0) {
        emulator.state.flags.o = 1;
        emulator.state.flags.c = 1;
        emulator.state.flags.z = 0;
        emulator.state.flags.n = 1;
        emulator.state.registers.a = 255;
      }
    }

    if (emulator.state.pc > 0xFFFF) {
      emulator.start_stop();
    }
  }
}

emulator.state.memory.get = function(address) 
{ 
  if (address >= 0xFF00) {
    return emulator.handle_input(address);
  }

  return (address >= 0x4000)
    ? emulator.state.memory.ram[address]
    : emulator.state.memory.rom[address];
};

emulator.state.memory.set = function(address, data) 
{
  if (address >= 0x4000) {
    if (address >= 0xFF00) {
      emulator.handle_output(address, data);
      return;
    }

    emulator.state.memory.ram[address] = data;
  }
};

emulator.ui.init = function()
{
  emulator.ui.objects.a = document.getElementById("ra");
  emulator.ui.objects.b = document.getElementById("rb");
  emulator.ui.objects.c = document.getElementById("rc");
  emulator.ui.objects.h = document.getElementById("rh");
  emulator.ui.objects.l = document.getElementById("rl");
  emulator.ui.objects.ir = document.getElementById("rir");

  emulator.ui.objects.sp = document.getElementById("sp");
  emulator.ui.objects.pc = document.getElementById("pc");

  emulator.ui.objects.fn = document.getElementById("fn");
  emulator.ui.objects.fz = document.getElementById("fz");
  emulator.ui.objects.fo = document.getElementById("fo");
  emulator.ui.objects.fc = document.getElementById("fc");

  emulator.ui.objects.textdisplay.obj = document.getElementById("textdisplay");

  emulator.ui.update();
};

emulator.ui.update = function()
{
  // Highlight the specified address in the disassembled code.
  if (emulator.state.pc != emulator.ui.prev_highlighted)
  {
    var address = emulator.state.pc;
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
      else {
        document.getElementById("assembly").scrollTop = 0;
      }
    }

    emulator.ui.prev_highlighted = address;
  }

  emulator.ui.objects.a.innerText = emulator.state.registers.a.toHex();
  emulator.ui.objects.b.innerText = emulator.state.registers.b.toHex();
  emulator.ui.objects.c.innerText = emulator.state.registers.c.toHex();
  emulator.ui.objects.h.innerText = emulator.state.registers.h.toHex();
  emulator.ui.objects.l.innerText = emulator.state.registers.l.toHex();
  emulator.ui.objects.ir.innerText = emulator.state.registers.ir.toHex();

  emulator.ui.objects.sp.innerText = emulator.state.sp.toHex(4);
  emulator.ui.objects.pc.innerText = emulator.state.pc.toHex(4);

  emulator.ui.objects.fn.className = "value v" + emulator.state.flags.n;
  emulator.ui.objects.fz.className = "value v" + emulator.state.flags.z;
  emulator.ui.objects.fo.className = "value v" + emulator.state.flags.o;
  emulator.ui.objects.fc.className = "value v" + emulator.state.flags.c;

  if (emulator.ui.objects.textdisplay.dirty) {
    emulator.ui.objects.textdisplay.obj.innerText = emulator.ui.objects.textdisplay.data;
    emulator.ui.objects.textdisplay.obj.scrollTop = emulator.ui.objects.textdisplay.obj.scrollHeight;
    emulator.ui.objects.textdisplay.dirty = false;
  }
}

emulator.ui.objects.textdisplay.print = function(str)
{
  emulator.ui.objects.textdisplay.data += str;
  emulator.ui.objects.textdisplay.dirty = true;
}

Number.prototype.toHex = function(len)
{
  var l = len > 0 ? len : 2;
  return "$" + this.toString(16).toUpperCase().padStart(l, '0');
}

document.getElementById("button_halt").addEventListener("click", emulator.halt);
document.getElementById("button_step").addEventListener("click", emulator.step);
document.getElementById("button_startstop").addEventListener("click", emulator.start_stop);
document.getElementById("iterations_per_update").addEventListener("change", function() { emulator.max_iterations = parseInt(this.value) });

document.getElementById("single_step").addEventListener("change", function() { 
  emulator.state.single_step = !emulator.state.single_step; 
  document.getElementById("button_step").disabled = !emulator.state.single_step; 
  document.getElementById("iterations_per_update").disabled = emulator.state.single_step;
});

document.write('<script type="text/javascript" src="js/example_program.js"></script>');
document.write('<script type="text/javascript" src="js/instructions.js"></script>');

document.addEventListener("DOMContentLoaded", emulator.init, true);