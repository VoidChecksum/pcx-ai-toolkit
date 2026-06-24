// Enma runtime trap scenario: out-of-bounds dynamic array access is catchable.

int64 main() {
    int64[] values = {1, 2};
    try {
        return values[4];
    } catch (string e) {
        return e.length();
    }
}
