function formatNida(val) {
    val = val.replace(/[^0-9]/g, '');
    if (val.length > 20) val = val.substring(0, 20);
    let formatted = val.substring(0, 8);
    if (val.length > 8) formatted += '-' + val.substring(8, 13);
    if (val.length > 13) formatted += '-' + val.substring(13, 18);
    if (val.length > 18) formatted += '-' + val.substring(18, 20);
    return formatted;
}

console.log(formatNida('22222222222222222222'));
console.log(formatNida('12345678123451234512'));
