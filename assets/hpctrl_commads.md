- po dokonceni kazdej sekvencie prikazov by mal program skocit von z cmd modu a pristroj ma byt stale v run mode (asi)

- at the beginning
```
osci
connect {int}
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

- getting preamble
```
q :waveform:preamble?
```

- single run (output on stdout)
```
cmd
s single
{ for channel in channels }
s :waveform:source channel{int}
s :waveform:data?
16
{ end loop }
s run
.
```

- continuous run (output in a file)
```
file {str}
cmd
...
.
```