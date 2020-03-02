namespace Emulator
{
    public class MemoryAccessRegister
    {
        public BusConnections BUS { get; set; }

        public Clock CLOCK { get; set; }

        public UInt16Value Value { get; set; }

        public bool H_load { get; set; }

        public bool L_load { get; set; }

        public bool PC_MAR_transfer { get; set; }

        public bool STK_MAR_transfer { get; set; }

        public void Tick()
        {
        }
    }
}