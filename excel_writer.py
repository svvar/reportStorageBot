import xlsxwriter


async def write_excel_to_buffer(sums: list, file):
    workbook = xlsxwriter.Workbook(file)
    worksheet = workbook.add_worksheet()

    format = workbook.add_format({'bg_color': '#FFFF00'})

    worksheet.write('A1', 'Дата и время', format)
    worksheet.write('B1', 'Категория', format)
    worksheet.write('C1', 'Сумма', format)

    last_row = 0
    total = 0
    if sums != []:
        for i, sum in enumerate(sums):
            worksheet.write(i+1, 0, sum[1].strftime('%d.%m.%Y %H:%M'))
            worksheet.write(i+1, 1, sum[0])
            worksheet.write(i+1, 2, str(sum[2]).replace('.', ','))
            last_row = i+1
            total += float(sum[2])

        worksheet.write(last_row+1, 0, 'Всего за отчетный период:', format)
        worksheet.write(last_row+1, 1, '', format)
        worksheet.write(last_row+1, 2, str(total).replace('.', ','), format)

    else:
        worksheet.write(1, 0, 'Нет новых данных', format)
    worksheet.autofit()
    workbook.close()



