- po dokonceni kazdej sekvencie prikazov by mal program skoncit v cmd mode a pristroj ma byt stale v run mode

- at the beginning
```
logon
osci
connect {int}
cmd
s run
s :waveform:format word
poff
```

- if average
```
s :acquire:average on
s :acquire:count {int}
s :acquire:points {int|auto}
```

- if not average
```
s :acquire:average off
```

- turning channels on and off
```
{ for channel in channels }
s :channel{int}:display {on/off}
{ end loop }
```

- single run (output on stdout)
```
s single
{ for channel in channels }
s :waveform:source channel{int}
s :waveform:data?
16
q :waveform:preamble?
{ end loop }
s run
```

- continuous run (output in a file)
```
.
file {str}
cmd
23 # select channel 2 and 3
*
?
q :waveform:preamble? (if not preamble)
```