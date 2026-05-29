cube(`Students`, {
  sql: `SELECT * FROM university.students`,
  measures: {
    count: { type: `count` },
  },
  dimensions: {
    studentId: { sql: `student_id`, type: `number`, primaryKey: true },
    faculty: { sql: `faculty`, type: `string` },
    groupName: { sql: `group_name`, type: `string` },
  },
});

cube(`Grades`, {
  sql: `SELECT * FROM university.grades`,
  measures: {
    avgGrade: { sql: `grade`, type: `avg` },
    count: { type: `count` },
  },
  dimensions: {
    gradeId: { sql: `grade_id`, type: `number`, primaryKey: true },
    subject: { sql: `subject`, type: `string` },
    faculty: { sql: `faculty`, type: `string` },
    groupName: { sql: `group_name`, type: `string` },
  },
});

cube(`RoomOccupancy`, {
  sql: `SELECT * FROM university.room_occupancy`,
  measures: {
    totalVisits: { sql: `count`, type: `sum` },
  },
  dimensions: {
    room: { sql: `room`, type: `string` },
    campus: { sql: `campus`, type: `string` },
  },
});
