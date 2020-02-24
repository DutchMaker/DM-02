namespace Emulator
{
    public class ProgramCounter
    {
        public BusConnections BUS { get; set; }

        public Clock CLOCK { get; set; }
        
        public UInt16Value Value { get; set; } = new UInt16Value();

        public bool H_load { get; set; }

        public bool L_load { get; set; }

        public bool H_out { get; set; }

        public bool L_out { get; set; }

        public bool Inc { get; set; }

        public bool PC_MAR_transfer { get; set; }

        public void Reset()
        {
            Value.Value = 0;
        }

        public void Tick()
        {
            if (CLOCK.CLOCK2_rising && Inc)
            {
                Value.Value++;
            }

            if (CLOCK.CLOCK2_rising && H_load)
            {
                Value.HighByte.Value = BUS.Data.Value;
            }

            if (CLOCK.CLOCK2_rising && L_load)
            {
                Value.LowByte.Value = BUS.Data.Value;
            }
        }
    }
}