#!/usr/bin/perl
use Data::Dumper;

sub getText {
	my ($url) = @_;
	chomp $url;
	my @text = qx{sh loadFromWeb3.sh $url};
	return @text
}


sub extract {
	my ($pron, $txt) = @_;
	my @verb;
	# mas pruebas, hacer en: https://regexr.com/
	for ($txt =~ /(presente|imperfecto( \(2\))?|futuro|condicional|simple)\n(\s|\w|[\(\)])+\($pron\)\s*(\w+)|imperativo\n(\s|\w|[\(\)])+\s(\w+)\s+\($pron\)/g) {
		s/(presente|imperfecto( \(2\))?|\(2\)|futuro|condicional|simple|imperativo)//;
		s/\W//;
		push(@verb,$_) if($_ =~ /\w+/);
	}
	
	return @verb;
}

sub reduce {
	my ($txt) = @_;
	my @parts = split(/\W/, $txt);
	my @out1;
	my @out2;
	my $n = 0;
	my %groups = ();
	my %counts = ();

	for my $word (@parts) {
		chomp $word;
		if ($word =~ /\w+/) {
			$groups{"$word"} = '';
		}
		$n = $n < length $word ? length $word : $n;
	}

	for (my $i=0; $i<$n; $i++) {
		my $expr = '';
		for my $word (keys %groups) {
			my $c = substr($word, $i-1, 1);
			grep {
				$expr = $_ if ($word =~ /^$_/);
			} values %groups;
			$expr = $expr eq '' ? $c : "$expr$c";
			#print "[$expr]\n";
			if ($word =~ /^$expr/) {
				$groups{$word} = $expr;
			}
		}

		map {
			$counts{$_}++;
		} values %groups;
	}

	my $key = '';
	my $val = 1;
	for my $k (sort(keys %counts)) {
		my $v = $counts{$k};
		if (length($k) >= length($key) && $v >= $val) {
			$key = $k;
			$val = $v;
		}
	}

	#print "\n$txt\n$n: $key - $val\n".Dumper(\%counts)."\n";

	my $flag = '';
	map {
		my $k = $_;
		if($k =~ /^$key/) {
			$k =~ s/$key//;
			if($k =~ /\w+/) {
				push @out2, $k;
			}
			else {
				$flag = '?';
			}
		}
		else {
			push @out1, $k;
		}
	} sort(keys %groups);

	push @out1, "$key(".join("|", @out2).")$flag";
	my $out = join("|", @out1);

	return ($out !~ /\w+/ ?$txt :$out);
}

######################################################3

sub extract2 {
	my ($txt) = @_;
	my @verb;
	# mas pruebas, hacer en: https://regexr.com/
	for ($txt =~ /(infinitivo|gerundio|participio pasado)\s+(\w+)\s+/g) {
		s/((infinitivo|gerundio|participio pasado))//;
		s/\W//;
		s/compuesto//;
		push(@verb,$_) if($_ =~ /\w+/);
	}
	
	return @verb;
}

sub Main {
	my ($verb) = @_;
	my $url = "http://conjugador.reverso.net/conjugacion-espanol.html?verb=$verb";

	my @text = getText($url);
	my $txt = join("\n", @text);
	$txt =~ s/(presente|preterito|futuro|condicional|imperativo|subjuntivo)/\(. . .\)\n $1/g;
	$txt =~ s/el ella ud[.]/el_la/g;
	$txt =~ s/ellos ellas uds[.]/elloas_uds/g;
	#print "$txt\n";
	
	my @yo = extract('yo',$txt);
	my @tu = extract('tu',$txt);
	my @el_la = extract('el_la',$txt);
	my @nos = extract('nosotros',$txt);
	my @uds = extract('vosotros',$txt);
	my @ellos = extract('elloas_uds',$txt);
	
	my $YO = reduce(join("|",@yo));
	my $TU = reduce(join("|",@tu));
	my $EL_LA = reduce(join("|",@el_la));
	my $NOS = reduce(join("|",@nos));
	my $UDS = reduce(join("|",@uds));
	my $ELLOS = reduce(join("|",@ellos));
	
	my @ip = (shift(@yo), shift(@tu), shift(@el_la), shift(@nos), shift(@uds), shift(@ellos));
	my @ipi = (shift(@yo), shift(@tu), shift(@el_la), shift(@nos), shift(@uds), shift(@ellos));
	my @if = (shift(@yo), shift(@tu), shift(@el_la), shift(@nos), shift(@uds), shift(@ellos));
	my @ic = (shift(@yo), shift(@tu), shift(@el_la), shift(@nos), shift(@uds), shift(@ellos));
	my @ipps = (shift(@yo), shift(@tu), shift(@el_la), shift(@nos), shift(@uds), shift(@ellos));
	
	my @sf = (pop(@yo), pop(@tu), pop(@el_la), pop(@nos), pop(@uds), pop(@ellos));
	my @spi2 = (pop(@yo), pop(@tu), pop(@el_la), pop(@nos), pop(@uds), pop(@ellos));
	my @spi = (pop(@yo), pop(@tu), pop(@el_la), pop(@nos), pop(@uds), pop(@ellos));
	my @sp = (pop(@yo), pop(@tu), pop(@el_la), pop(@nos), pop(@uds), pop(@ellos));
	
	my @i = (pop(@yo), pop(@tu), pop(@el_la), pop(@nos), pop(@uds), pop(@ellos));
	
	my $IP = reduce(join("|",@ip));
	my $IPI = reduce(join("|",@ipi));
	my $IF = reduce(join("|",@if));
	my $IC = reduce(join("|",@ic));
	my $I = reduce(join("|",@i));
	my $IPPS = reduce(join("|",@ipps));
	my $SF = reduce(join("|",@sf));
	my $SPI2 = reduce(join("|",@spi2));
	my $SPI = reduce(join("|",@spi));
	my $SP = reduce(join("|",@sp));
	
	my @igp = extract2($txt);
	my ($ger,$par,$inf) = @igp;
	
	print qq{"inf"   : "$inf",\n};
	print qq{"ger"   : "$ger",\n};
	print qq{"par"   : "$par",\n};

	print qq{"ip"    : "$IP",\n};
	print qq{"ipi"   : "$IPI",\n};
	print qq{"if"    : "$IF",\n};
	print qq{"ic"    : "$IC",\n};
	print qq{"ipps"  : "$IPPS",\n};

	print qq{"i"     : "$I",\n};

	print qq{"sp"    : "$SP",\n};
	print qq{"spi"   : "$SPI",\n};
	print qq{"spi2"  : "$SPI2",\n};
	print qq{"sf"    : "$SF",\n};
	
	print qq{"yo"    : "$YO",\n};
	print qq{"tu"    : "$TU",\n};
	print qq{"el_la" : "$EL_LA",\n};
	print qq{"nos"   : "$NOS",\n};
	print qq{"uds"   : "$UDS",\n};
	print qq{"ellos" : "$ELLOS"\n};
	
	reduce($I);
}

my ($verb) = @ARGV;
chomp $verb;

Main ($verb);
