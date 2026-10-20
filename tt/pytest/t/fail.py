from Pyjo.Test import done_testing, is_ok, subtest


is_ok(1, 1, 'same')

with subtest('Group'):
    is_ok(200, 404, 'right status')

done_testing()
